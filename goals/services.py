"""Personal goal progress rules (member 4)."""
from django.db import transaction
from django.db.models import Q, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone

from actions.models import ActionSubmission
from analytics.activity import log_activity
from analytics.models import ActivityLog
from core.exceptions import BusinessRuleError
from gamification.models import PointTransaction
from notifications.models import Notification
from notifications.services import notify

from .models import Goal


def compute_automatic_progress(goal):
    """Progress of an automatic goal, computed only from verified records."""
    if goal.tracking_mode == Goal.TrackingMode.ACTIONS:
        qs = ActionSubmission.objects.filter(
            user=goal.user, status=ActionSubmission.Status.APPROVED,
            performed_on__gte=goal.start_date, performed_on__lte=goal.deadline,
        )
        if goal.category:
            qs = qs.filter(action_type__category=goal.category)
        return qs.count()
    if goal.tracking_mode == Goal.TrackingMode.POINTS:
        qs = PointTransaction.objects.filter(
            user=goal.user, created_at__date__gte=goal.start_date, created_at__date__lte=goal.deadline,
        )
        if goal.category:
            qs = qs.filter(Q(submission__action_type__category=goal.category) | Q(challenge__category=goal.category))
        return max(0, qs.aggregate(total=Coalesce(Sum('amount'), 0))['total'])
    return goal.current_progress


def apply_progress(goal, value):
    """Store a new progress value and handle milestones and completion."""
    old_percent = goal.progress_percent if goal.pk else 0
    goal.current_progress = max(0, value)
    reached = goal.current_progress >= goal.target_value
    just_completed = False
    if goal.status == Goal.Status.ACTIVE and reached:
        goal.status = Goal.Status.COMPLETED
        goal.completed_at = timezone.now()
        just_completed = True
    elif goal.status == Goal.Status.COMPLETED and not reached:
        goal.status = Goal.Status.ACTIVE
        goal.completed_at = None
    goal.save()
    if just_completed:
        notify(goal.user, Notification.Kind.GOAL, 'Objectif atteint !',
               f'Félicitations, vous avez atteint votre objectif « {goal.title} ».', goal.get_absolute_url())
        log_activity(goal.user, ActivityLog.Verb.GOAL_COMPLETED,
                     f'{goal.user.display_name} a atteint son objectif « {goal.title} ».', link=goal.get_absolute_url())
    elif goal.status == Goal.Status.ACTIVE and old_percent < 50 <= goal.progress_percent:
        notify(goal.user, Notification.Kind.GOAL, 'À mi-chemin de votre objectif',
               f'Vous avez dépassé 50 % de votre objectif « {goal.title} ». Continuez !', goal.get_absolute_url())
    return just_completed


def refresh_auto_goals(user):
    goals = Goal.objects.filter(user=user, status__in=[Goal.Status.ACTIVE, Goal.Status.COMPLETED]).exclude(
        tracking_mode=Goal.TrackingMode.MANUAL
    )
    for goal in goals:
        value = compute_automatic_progress(goal)
        if value != goal.current_progress:
            apply_progress(goal, value)


@transaction.atomic
def save_goal(user, form):
    """Create or update a goal from a validated ``GoalForm`` owned by ``user``."""
    from gamification.services import evaluate_badges

    goal = form.save(commit=False)
    is_new = goal.pk is None
    if is_new:
        goal.user = user
    elif goal.user_id != user.pk:
        raise BusinessRuleError('Vous ne pouvez modifier que vos propres objectifs.')
    value = compute_automatic_progress(goal) if goal.is_automatic else goal.current_progress
    if goal.status == Goal.Status.ABANDONED:
        goal.current_progress = value
        goal.save()
    else:
        apply_progress(goal, value)
    if is_new:
        log_activity(user, ActivityLog.Verb.GOAL_CREATED, f'{user.display_name} s’est fixé l’objectif « {goal.title} ».',
                     link=goal.get_absolute_url())
    evaluate_badges(user)
    return goal


@transaction.atomic
def update_manual_progress(user, goal, value):
    from gamification.services import evaluate_badges

    if goal.user_id != user.pk:
        raise BusinessRuleError('Vous ne pouvez modifier que vos propres objectifs.')
    if goal.is_automatic:
        raise BusinessRuleError('Cet objectif est suivi automatiquement à partir de vos actions validées.')
    if goal.status == Goal.Status.ABANDONED:
        raise BusinessRuleError('Réactivez cet objectif avant de mettre à jour sa progression.')
    apply_progress(goal, value)
    evaluate_badges(user)
    return goal


@transaction.atomic
def set_abandoned(user, goal, abandoned):
    if goal.user_id != user.pk:
        raise BusinessRuleError('Vous ne pouvez modifier que vos propres objectifs.')
    if abandoned:
        if goal.status == Goal.Status.COMPLETED:
            raise BusinessRuleError('Un objectif atteint ne peut pas être abandonné.')
        goal.status = Goal.Status.ABANDONED
        goal.save(update_fields=['status', 'updated_at'])
    else:
        goal.status = Goal.Status.ACTIVE
        value = compute_automatic_progress(goal) if goal.is_automatic else goal.current_progress
        apply_progress(goal, value)
    return goal
