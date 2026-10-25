"""Ecological action submissions and moderation (member 3)."""
from django.db import IntegrityError, transaction
from django.utils import timezone

from analytics.activity import log_activity
from analytics.models import ActivityLog
from core.exceptions import BusinessRuleError
from core.permissions import MODERATE_ACTIONS
from gamification.models import PointTransaction
from gamification.services import award_points
from notifications.models import Notification
from notifications.services import notify
from teams.services import get_user_team

from .models import ActionSubmission, ModerationLog


def ai_validate_submission(submission):
    """Return an advisory AI report; this deliberately has no moderation side effects."""
    from .ai_validator import validate_submission

    return validate_submission(submission)


def can_moderate(user):
    return user.is_authenticated and user.is_active and user.has_perm(MODERATE_ACTIONS)


def can_view_submission(user, submission):
    return submission.user_id == user.pk or can_moderate(user)


@transaction.atomic
def create_submission(user, form):
    submission = form.save(commit=False)
    submission.user = user
    submission.status = ActionSubmission.Status.PENDING
    submission.points_awarded = 0
    try:
        with transaction.atomic():
            submission.save()
    except IntegrityError as exc:
        # L'index unique sur dedupe_key rattrape les doublons que la
        # validation du formulaire n'a pas vus (deux envois simultanés).
        raise BusinessRuleError(
            'Vous avez déjà déclaré cette action pour cette date.'
        ) from exc
    log_activity(user, ActivityLog.Verb.ACTION_SUBMITTED,
                 f'{user.display_name} a déclaré l’action « {submission.action_type.name} ».',
                 link=submission.get_absolute_url())
    return submission


def update_submission(user, submission, form):
    if submission.user_id != user.pk:
        raise BusinessRuleError('Vous ne pouvez modifier que vos propres déclarations.')
    if not submission.is_editable:
        raise BusinessRuleError('Une déclaration déjà modérée ne peut plus être modifiée.')
    try:
        with transaction.atomic():
            return form.save()
    except IntegrityError as exc:
        raise BusinessRuleError(
            'Vous avez déjà déclaré cette action pour cette date.'
        ) from exc


@transaction.atomic
def delete_submission(user, submission):
    if submission.user_id != user.pk:
        raise BusinessRuleError('Vous ne pouvez supprimer que vos propres déclarations.')
    if not submission.is_editable:
        raise BusinessRuleError('Une déclaration déjà modérée ne peut pas être supprimée.')
    evidence = submission.evidence
    submission.delete()
    if evidence:
        transaction.on_commit(lambda: evidence.delete(save=False))


def _lock_for_moderation(moderator, submission, expected_status):
    if not can_moderate(moderator):
        raise BusinessRuleError('Vous n’êtes pas autorisé·e à modérer les déclarations.')
    locked = (
        ActionSubmission.objects.select_for_update()
        .select_related('action_type', 'user', 'challenge')
        .get(pk=submission.pk)
    )
    if locked.user_id == moderator.pk:
        raise BusinessRuleError('Vous ne pouvez pas modérer vos propres déclarations.')
    if locked.status != expected_status:
        raise BusinessRuleError('Cette déclaration a déjà été traitée par un autre modérateur.')
    return locked


def approve_submission(moderator, submission, notes=''):
    """Approve a pending submission and award its fixed points exactly once."""
    from challenges.services import notify_if_ready

    with transaction.atomic():
        sub = _lock_for_moderation(moderator, submission, ActionSubmission.Status.PENDING)
        team = get_user_team(sub.user)
        points = sub.action_type.points
        sub.status = ActionSubmission.Status.APPROVED
        sub.points_awarded = points
        sub.co2_saved_kg = sub.action_type.estimate_co2(sub.quantity)
        sub.team = team
        sub.reviewed_by = moderator
        sub.reviewed_at = timezone.now()
        sub.moderation_notes = notes.strip()
        sub.save()
        ModerationLog.objects.create(
            submission=sub, moderator=moderator, decision=ModerationLog.Decision.APPROVED,
            previous_status=ActionSubmission.Status.PENDING, new_status=sub.status,
            notes=sub.moderation_notes, points_delta=points,
        )
        log_activity(sub.user, ActivityLog.Verb.ACTION_APPROVED,
                     f'Action validée : « {sub.action_type.name} » (+{points} pts).', team=team,
                     link=sub.get_absolute_url())
        notify(sub.user, Notification.Kind.ACTION, 'Action validée',
               f'Votre action « {sub.action_type.name} » a été validée par la modération.', sub.get_absolute_url())
        award_points(
            user=sub.user, amount=points, reason=PointTransaction.Reason.ACTION_APPROVED,
            reference=f'action:{sub.pk}', submission=sub, team=team,
            description=f'Action validée : {sub.action_type.name}',
        )
        if sub.challenge_id:
            notify_if_ready(sub.user, sub.challenge)
    return sub


@transaction.atomic
def reject_submission(moderator, submission, reason):
    if not reason.strip():
        raise BusinessRuleError('Le motif du refus est obligatoire.')
    sub = _lock_for_moderation(moderator, submission, ActionSubmission.Status.PENDING)
    sub.status = ActionSubmission.Status.REJECTED
    sub.reviewed_by = moderator
    sub.reviewed_at = timezone.now()
    sub.moderation_notes = reason.strip()
    sub.save()
    ModerationLog.objects.create(
        submission=sub, moderator=moderator, decision=ModerationLog.Decision.REJECTED,
        previous_status=ActionSubmission.Status.PENDING, new_status=sub.status, notes=sub.moderation_notes,
    )
    log_activity(sub.user, ActivityLog.Verb.ACTION_REJECTED, f'Action refusée : « {sub.action_type.name} ».',
                 link=sub.get_absolute_url())
    notify(sub.user, Notification.Kind.ACTION, 'Action refusée',
           f'« {sub.action_type.name} » a été refusée : {sub.moderation_notes}', sub.get_absolute_url())
    return sub


@transaction.atomic
def revoke_approval(moderator, submission, reason):
    """Exceptional, audited correction: cancels an approval with a reversing ledger entry."""
    if not reason.strip():
        raise BusinessRuleError('Le motif de l’annulation est obligatoire.')
    sub = _lock_for_moderation(moderator, submission, ActionSubmission.Status.APPROVED)
    points = sub.points_awarded
    credited_team = sub.team
    sub.status = ActionSubmission.Status.REJECTED
    sub.moderation_notes = f'Validation annulée : {reason.strip()}'
    sub.points_awarded = 0
    sub.co2_saved_kg = None
    sub.reviewed_by = moderator
    sub.reviewed_at = timezone.now()
    sub.save()
    ModerationLog.objects.create(
        submission=sub, moderator=moderator, decision=ModerationLog.Decision.REVOKED,
        previous_status=ActionSubmission.Status.APPROVED, new_status=sub.status,
        notes=reason.strip(), points_delta=-points,
    )
    log_activity(sub.user, ActivityLog.Verb.ACTION_REVOKED,
                 f'Validation annulée : « {sub.action_type.name} » ({-points} pts).', team=credited_team,
                 link=sub.get_absolute_url())
    notify(sub.user, Notification.Kind.ACTION, 'Validation annulée',
           f'La validation de « {sub.action_type.name} » a été annulée : {reason.strip()}', sub.get_absolute_url())
    if points:
        award_points(
            user=sub.user, amount=-points, reason=PointTransaction.Reason.ACTION_REVOKED,
            reference=f'action:{sub.pk}:revoke', submission=sub, team=credited_team,
            description=f'Annulation de validation : {sub.action_type.name}',
        )
    return sub
