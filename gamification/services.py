"""Central scoring service (member 4).

This module is the only place that writes the points ledger. Every module
(actions, challenges, administration) calls :func:`award_points`, which is
idempotent thanks to the unique ``reference`` of each transaction.
"""
import logging
from uuid import uuid4

from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models import Count, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone

from analytics.activity import log_activity
from analytics.models import ActivityLog
from core.exceptions import BusinessRuleError
from core.utils import percent
from notifications.models import Notification
from notifications.services import notify, notify_many
from teams.models import Team
from teams.services import get_user_team

from .models import Badge, PointTransaction, UserBadge

logger = logging.getLogger('ecoteams')

CURRENT_TEAM = object()
MAX_ADJUSTMENT = 1000


def user_points(user):
    return PointTransaction.objects.filter(user=user).aggregate(total=Coalesce(Sum('amount'), 0))['total']


def team_points(team):
    if team is None:
        return 0
    return PointTransaction.objects.filter(team=team).aggregate(total=Coalesce(Sum('amount'), 0))['total']


def team_rank(team):
    """Rank of ``team`` among non-archived teams by ledger points (None if no points)."""
    if team is None:
        return None
    totals = list(
        PointTransaction.objects.filter(team__isnull=False)
        .exclude(team__status=Team.Status.ARCHIVED)
        .values('team')
        .annotate(total=Sum('amount'))
    )
    mine = next((row['total'] for row in totals if row['team'] == team.pk), 0)
    if mine <= 0:
        return None
    return 1 + sum(1 for row in totals if row['total'] > mine)


def award_points(*, user, amount, reason, reference, description, submission=None, challenge=None,
                 created_by=None, team=CURRENT_TEAM, notify_user=True):
    """Record a ledger entry exactly once. Returns the entry, or None if it already existed."""
    if not amount:
        raise ValueError('Une transaction de points ne peut pas être nulle.')
    if team is CURRENT_TEAM:
        team = get_user_team(user)
    with transaction.atomic():
        if PointTransaction.objects.filter(reference=reference).exists():
            return None
        team_before = team_points(team)
        try:
            with transaction.atomic():
                entry = PointTransaction.objects.create(
                    user=user, team=team, amount=amount, reason=reason, reference=reference,
                    description=description[:255], submission=submission, challenge=challenge,
                    created_by=created_by,
                )
        except IntegrityError:
            logger.info('Duplicate points reference ignored: %s', reference)
            return None
        if notify_user:
            sign = '+' if amount > 0 else ''
            notify(user, Notification.Kind.POINTS, f'{sign}{amount} points', description, '/history/')
        refresh_scores(user)
        if team is not None and amount > 0:
            _after_team_gain(team, team_before, team_before + amount, exclude=user)
    return entry


def _after_team_gain(team, before, after, exclude=None):
    members = list(team.members.filter(is_active=True))
    for milestone in settings.ECOTEAMS_TEAM_MILESTONES:
        if before < milestone <= after:
            notify_many(
                members, Notification.Kind.LEADERBOARD, f'Cap des {milestone} points franchi !',
                f'L’équipe « {team.name} » totalise désormais {after} points. Bravo à toute l’équipe !',
                '/leaderboard/',
            )
    if team_rank(team) == 1:
        for member in members:
            if exclude is None or member.pk != exclude.pk:
                evaluate_badges(member)


def refresh_scores(user):
    """Recompute everything derived from a user's activity (goals, badges)."""
    from goals.services import refresh_auto_goals

    refresh_auto_goals(user)
    evaluate_badges(user)


@transaction.atomic
def adjust_points(*, admin, user, amount, reason):
    """Audited manual correction, restricted to authorised administrators."""
    if not (admin.is_active and admin.has_perm('gamification.adjust_points')):
        raise BusinessRuleError('Vous n’êtes pas autorisé·e à corriger des points.')
    if admin.pk == user.pk and not admin.is_superuser:
        raise BusinessRuleError('Vous ne pouvez pas corriger vos propres points.')
    if amount == 0 or abs(amount) > MAX_ADJUSTMENT:
        raise BusinessRuleError(f'La correction doit être comprise entre -{MAX_ADJUSTMENT} et {MAX_ADJUSTMENT} points (hors 0).')
    if not reason.strip():
        raise BusinessRuleError('Le motif de la correction est obligatoire.')
    if user_points(user) + amount < 0:
        raise BusinessRuleError('Une correction ne peut pas rendre le solde de points négatif.')
    entry = award_points(
        user=user, amount=amount, reason=PointTransaction.Reason.MANUAL_ADJUSTMENT,
        reference=f'adjust:{uuid4().hex}', description=f'Correction administrative : {reason.strip()}',
        created_by=admin,
    )
    log_activity(admin, ActivityLog.Verb.POINTS_ADJUSTED,
                 f'Correction de {amount:+d} points pour {user.display_name} : {reason.strip()}', team=None)
    return entry


# --- Streaks and badges ----------------------------------------------------

def compute_streaks(user):
    from actions.models import ActionSubmission

    dates = sorted(set(
        ActionSubmission.objects.filter(user=user, status=ActionSubmission.Status.APPROVED)
        .values_list('performed_on', flat=True)
    ))
    best = run = 0
    previous = None
    for day in dates:
        run = run + 1 if previous is not None and (day - previous).days == 1 else 1
        best = max(best, run)
        previous = day
    current = run if previous is not None and (timezone.localdate() - previous).days <= 1 else 0
    return {'current': current, 'best': best, 'last_day': previous}


def badge_metrics(user, rules=None):
    from actions.models import ActionSubmission
    from challenges.models import ChallengeParticipation
    from community.models import EventParticipation
    from goals.models import Goal

    rules = set(rules or Badge.Rule.values)
    metrics = {}
    approved = ActionSubmission.objects.filter(user=user, status=ActionSubmission.Status.APPROVED)
    if Badge.Rule.ACTIONS_TOTAL in rules:
        metrics[Badge.Rule.ACTIONS_TOTAL] = approved.count()
    if Badge.Rule.CATEGORY_ACTIONS in rules:
        metrics[Badge.Rule.CATEGORY_ACTIONS] = dict(
            approved.values_list('action_type__category').annotate(total=Count('pk'))
        )
    if Badge.Rule.POINTS_TOTAL in rules:
        metrics[Badge.Rule.POINTS_TOTAL] = user_points(user)
    if Badge.Rule.STREAK_DAYS in rules:
        metrics[Badge.Rule.STREAK_DAYS] = compute_streaks(user)['best']
    if Badge.Rule.CHALLENGES_COMPLETED in rules:
        metrics[Badge.Rule.CHALLENGES_COMPLETED] = ChallengeParticipation.objects.filter(
            user=user, status=ChallengeParticipation.Status.COMPLETED
        ).count()
    if Badge.Rule.GOALS_COMPLETED in rules:
        metrics[Badge.Rule.GOALS_COMPLETED] = Goal.objects.filter(user=user, status=Goal.Status.COMPLETED).count()
    if Badge.Rule.EVENTS_JOINED in rules:
        metrics[Badge.Rule.EVENTS_JOINED] = EventParticipation.objects.filter(user=user).count()
    if Badge.Rule.TEAM_RANK in rules:
        metrics[Badge.Rule.TEAM_RANK] = team_rank(get_user_team(user))
    return metrics


def badge_value(badge, metrics):
    if badge.rule == Badge.Rule.CATEGORY_ACTIONS:
        return metrics.get(Badge.Rule.CATEGORY_ACTIONS, {}).get(badge.category, 0)
    return metrics.get(badge.rule)


def is_badge_unlocked(badge, metrics):
    value = badge_value(badge, metrics)
    if badge.rule == Badge.Rule.TEAM_RANK:
        return value is not None and value <= badge.threshold
    return (value or 0) >= badge.threshold


def evaluate_badges(user):
    """Award every active badge the user is now eligible for. Returns new badges."""
    earned = set(UserBadge.objects.filter(user=user).values_list('badge_id', flat=True))
    candidates = [badge for badge in Badge.objects.filter(is_active=True) if badge.pk not in earned]
    if not candidates:
        return []
    metrics = badge_metrics(user, {badge.rule for badge in candidates})
    unlocked = []
    for badge in candidates:
        if not is_badge_unlocked(badge, metrics):
            continue
        _, created = UserBadge.objects.get_or_create(user=user, badge=badge)
        if created:
            unlocked.append(badge)
            notify(user, Notification.Kind.BADGE, f'Badge débloqué : {badge.name}', badge.description, '/achievements/')
            log_activity(user, ActivityLog.Verb.BADGE_UNLOCKED,
                         f'{user.display_name} a débloqué le badge « {badge.name} ».', link='/achievements/')
    return unlocked


def badge_progress(user):
    """Every active badge with the user's progress toward it."""
    awards = {award.badge_id: award for award in UserBadge.objects.filter(user=user)}
    badges = list(Badge.objects.filter(is_active=True))
    metrics = badge_metrics(user, {badge.rule for badge in badges})
    rows = []
    for badge in badges:
        value = badge_value(badge, metrics)
        award = awards.get(badge.pk)
        if badge.rule == Badge.Rule.TEAM_RANK:
            progress = 100 if award or (value is not None and value <= badge.threshold) else (
                percent(badge.threshold, value) if value else 0
            )
            label = f'Rang actuel : {value}' if value else 'Équipe non classée'
        else:
            progress = 100 if award else percent(value or 0, badge.threshold)
            label = f'{value or 0} / {badge.threshold}'
        rows.append({'badge': badge, 'award': award, 'value': value, 'progress': progress, 'label': label})
    rows.sort(key=lambda row: (row['award'] is None, -row['progress'], row['badge'].threshold))
    return rows
