"""Statistics, leaderboard and dashboards (member 5).

Every number shown in EcoTeams is computed here from database records:
points come from the ledger, actions from approved submissions, CO₂ values
from the configured factors of the action catalogue (always labelled as
estimates).
"""
from datetime import timedelta
from decimal import Decimal

from django.db.models import Case, Count, DecimalField, IntegerField, OuterRef, Q, Subquery, Sum, Value, When
from django.db.models.functions import Coalesce, TruncDate
from django.utils import timezone

from accounts.models import User
from actions.models import ActionSubmission
from challenges.models import Challenge, ChallengeParticipation
from community.models import Event, EventParticipation
from core.choices import EcoCategory
from core.utils import percent
from gamification.models import Badge, PointTransaction, UserBadge
from gamification.services import compute_streaks, team_rank, user_points
from goals.models import Goal
from teams.models import Membership, Team
from teams.services import get_user_team

from .models import ActivityLog

PERIODS = {
    'all': 'Depuis le début',
    'month': '30 derniers jours',
    'week': '7 derniers jours',
}
LEADERBOARD_SORTS = {
    'points': 'Points',
    'members': 'Membres',
    'actions': 'Actions validées',
    'challenges': 'Défis réussis',
    'name': 'Nom',
}
ZERO_DECIMAL = Value(Decimal('0'), output_field=DecimalField(max_digits=14, decimal_places=3))


def period_start(period):
    days = {'week': 7, 'month': 30, 'quarter': 90, 'year': 365}.get(period)
    return timezone.now() - timedelta(days=days) if days else None


def _sum_subquery(qs, field, output_field=None):
    output_field = output_field or IntegerField()
    sub = qs.order_by().values('team').annotate(total=Sum(field)).values('total')[:1]
    fallback = ZERO_DECIMAL if isinstance(output_field, DecimalField) else Value(0)
    return Coalesce(Subquery(sub, output_field=output_field), fallback, output_field=output_field)


def _count_subquery(qs):
    sub = qs.order_by().values('team').annotate(total=Count('pk')).values('total')[:1]
    return Coalesce(Subquery(sub, output_field=IntegerField()), Value(0))


def annotate_team_stats(queryset):
    """Add ``points`` (ledger) and ``member_total`` to a Team queryset."""
    return queryset.annotate(
        points=_sum_subquery(PointTransaction.objects.filter(team=OuterRef('pk')), 'amount'),
        member_total=_count_subquery(Membership.objects.filter(team=OuterRef('pk'))),
    )


def team_leaderboard(period='all', category='', sort='points', organization=None, viewer=None, public_only=False):
    """Teams ranked by the points recorded in the ledger (competition ranking).

    ``organization`` restricts the board to the workplace teams of one organization;
    ``viewer`` hides the workplace teams of organizations the viewer does not belong to
    (administrators see everything); ``public_only`` is used by the public landing page.
    """
    since = period_start(period)
    ledger = PointTransaction.objects.filter(team=OuterRef('pk'))
    actions = ActionSubmission.objects.filter(team=OuterRef('pk'), status=ActionSubmission.Status.APPROVED)
    challenges = ChallengeParticipation.objects.filter(
        team=OuterRef('pk'), status=ChallengeParticipation.Status.COMPLETED
    )
    if since:
        ledger = ledger.filter(created_at__gte=since)
        actions = actions.filter(reviewed_at__gte=since)
        challenges = challenges.filter(completed_at__gte=since)
    if category:
        ledger = ledger.filter(Q(submission__action_type__category=category) | Q(challenge__category=category))
        actions = actions.filter(action_type__category=category)
        challenges = challenges.filter(challenge__category=category)

    teams = (
        Team.objects.exclude(status=Team.Status.ARCHIVED)
        .select_related('captain')
        .annotate(
            points=_sum_subquery(ledger, 'amount'),
            member_total=_count_subquery(Membership.objects.filter(team=OuterRef('pk'))),
            approved_actions=_count_subquery(actions),
            completed_challenges=_count_subquery(challenges),
            co2_estimate=_sum_subquery(actions, 'co2_saved_kg', DecimalField(max_digits=14, decimal_places=3)),
        )
        .order_by('-points', 'name')
    )
    if organization is not None:
        teams = teams.filter(organization=organization)
    elif public_only:
        teams = teams.filter(organization__isnull=True)
    elif viewer is not None and not viewer.is_superuser:
        teams = teams.filter(Q(organization__isnull=True) | Q(organization_id=viewer.affiliation_id))
    rows = list(teams)
    rank, previous = 0, None
    for index, team in enumerate(rows, start=1):
        if team.points != previous:
            rank, previous = index, team.points
        team.rank = rank
    leader_points = rows[0].points if rows and rows[0].points > 0 else 0
    for team in rows:
        target = team.goal_points or leader_points
        team.progress = percent(team.points, target) if target else 0
    sort_keys = {
        'members': lambda t: (-t.member_total, t.rank),
        'actions': lambda t: (-t.approved_actions, t.rank),
        'challenges': lambda t: (-t.completed_challenges, t.rank),
        'name': lambda t: t.name.lower(),
    }
    if sort in sort_keys:
        rows.sort(key=sort_keys[sort])
    return rows


def user_leaderboard(period='all', limit=10):
    since = period_start(period)
    condition = Q(point_transactions__created_at__gte=since) if since else Q()
    return list(
        # Employees never appear in the individual board: their results stay private to their organization.
        User.objects.filter(is_active=True).exclude(organization_type=User.OrganizationType.EMPLOYEE)
        .annotate(total=Coalesce(Sum('point_transactions__amount', filter=condition), 0))
        .filter(total__gt=0)
        .order_by('-total', 'username')[:limit]
    )


def user_rank(user):
    total = user_points(user)
    if total <= 0:
        return None
    higher = (
        User.objects.filter(is_active=True)
        .annotate(total=Sum('point_transactions__amount'))
        .filter(total__gt=total)
        .count()
    )
    return higher + 1


# --- Time series ------------------------------------------------------------

def daily_points(ledger_qs, days=7):
    start = timezone.localdate() - timedelta(days=days - 1)
    rows = (
        ledger_qs.filter(created_at__date__gte=start)
        .annotate(day=TruncDate('created_at'))
        .order_by()
        .values('day')
        .annotate(total=Sum('amount'))
    )
    totals = {row['day']: row['total'] for row in rows}
    labels = ['lun.', 'mar.', 'mer.', 'jeu.', 'ven.', 'sam.', 'dim.']
    series = []
    for offset in range(days):
        day = start + timedelta(days=offset)
        series.append({'label': f'{labels[day.weekday()]} {day:%d}', 'value': totals.get(day, 0)})
    return series


def weekly_series(qs, date_field, weeks=8, value=None):
    """Weekly totals for the last ``weeks`` weeks (count, or sum of ``value``)."""
    today = timezone.localdate()
    start = today - timedelta(days=today.weekday()) - timedelta(weeks=weeks - 1)
    aggregate = Sum(value) if value else Count('pk')
    rows = (
        qs.filter(**{f'{date_field}__date__gte': start})
        .annotate(day=TruncDate(date_field))
        .order_by()
        .values('day')
        .annotate(total=aggregate)
    )
    buckets = [0] * weeks
    for row in rows:
        index = (row['day'] - start).days // 7
        if 0 <= index < weeks:
            buckets[index] += row['total'] or 0
    return [
        {'label': f'{start + timedelta(weeks=i):%d/%m}',
         'value': float(buckets[i]) if isinstance(buckets[i], Decimal) else buckets[i]}
        for i in range(weeks)
    ]


def category_breakdown(submissions):
    rows = {
        row['action_type__category']: row
        for row in submissions.order_by().values('action_type__category').annotate(
            count=Count('pk'),
            points=Coalesce(Sum('points_awarded'), 0),
            co2=Coalesce(Sum('co2_saved_kg'), ZERO_DECIMAL),
        )
    }
    result = []
    for value, label in EcoCategory.choices:
        row = rows.get(value, {})
        result.append({
            'category': value, 'label': label, 'count': row.get('count', 0),
            'points': row.get('points', 0), 'co2': row.get('co2', Decimal('0')),
        })
    return result


def approved_co2(submissions):
    return submissions.filter(status=ActionSubmission.Status.APPROVED).aggregate(
        total=Coalesce(Sum('co2_saved_kg'), ZERO_DECIMAL)
    )['total']


# --- Dashboards -------------------------------------------------------------

def suggested_challenges(user, limit=3):
    joined = ChallengeParticipation.objects.filter(user=user).exclude(
        status=ChallengeParticipation.Status.ABANDONED
    ).values('challenge_id')
    qs = Challenge.objects.filter(status=Challenge.Status.ACTIVE, end_date__gte=timezone.localdate()).exclude(
        pk__in=joined
    )
    if user.favorite_category:
        qs = qs.annotate(
            preferred=Case(When(category=user.favorite_category, then=Value(0)), default=Value(1))
        ).order_by('preferred', 'end_date')
    else:
        qs = qs.order_by('end_date')
    return list(qs[:limit])


def user_dashboard(user):
    from challenges.services import participation_progress

    team = get_user_team(user)
    submissions = ActionSubmission.objects.filter(user=user)
    status_counts = dict(submissions.order_by().values_list('status').annotate(total=Count('pk')))
    ledger = PointTransaction.objects.filter(user=user)
    today = timezone.localdate()
    week_start = today - timedelta(days=6)
    this_week = submissions.filter(status=ActionSubmission.Status.APPROVED, performed_on__gte=week_start).count()
    last_week = submissions.filter(
        status=ActionSubmission.Status.APPROVED,
        performed_on__gte=week_start - timedelta(days=7), performed_on__lt=week_start,
    ).count()
    participations = list(
        ChallengeParticipation.objects.filter(user=user, status=ChallengeParticipation.Status.IN_PROGRESS)
        .select_related('challenge')[:4]
    )
    for participation in participations:
        participation.progress = participation_progress(participation)
    goals = list(Goal.objects.filter(user=user, status=Goal.Status.ACTIVE).order_by('deadline')[:4])
    return {
        'team': team,
        'points': user_points(user),
        'rank': user_rank(user),
        'team_rank': team_rank(team),
        'team_points': None if team is None else PointTransaction.objects.filter(team=team).aggregate(
            total=Coalesce(Sum('amount'), 0))['total'],
        'approved_count': status_counts.get(ActionSubmission.Status.APPROVED, 0),
        'pending_count': status_counts.get(ActionSubmission.Status.PENDING, 0),
        'rejected_count': status_counts.get(ActionSubmission.Status.REJECTED, 0),
        'co2': approved_co2(submissions),
        'this_week_actions': this_week,
        'last_week_actions': last_week,
        'daily_points': daily_points(ledger, 7),
        'weekly_points': weekly_series(ledger, 'created_at', 8, 'amount'),
        'participations': participations,
        'challenges_in_progress': ChallengeParticipation.objects.filter(
            user=user, status=ChallengeParticipation.Status.IN_PROGRESS).count(),
        'challenges_completed': ChallengeParticipation.objects.filter(
            user=user, status=ChallengeParticipation.Status.COMPLETED).count(),
        'goals': goals,
        'goals_completed': Goal.objects.filter(user=user, status=Goal.Status.COMPLETED).count(),
        'badges_count': UserBadge.objects.filter(user=user).count(),
        'badges_total': Badge.objects.filter(is_active=True).count(),
        'recent_badges': list(UserBadge.objects.filter(user=user).select_related('badge')[:4]),
        'activities': list(ActivityLog.objects.filter(actor=user).select_related('team')[:6]),
        'streak': compute_streaks(user),
        'upcoming_events': list(
            Event.objects.filter(participations__user=user, status=Event.Status.PUBLISHED, end_at__gte=timezone.now())
            .order_by('start_at')[:3]
        ),
        'suggested_challenges': suggested_challenges(user, limit=4),
        'recent_actions': list(submissions.select_related('action_type').order_by('-created_at')[:5]),
        'team_contribution': percent(
            ledger.filter(team=team).aggregate(total=Coalesce(Sum('amount'), 0))['total'],
            PointTransaction.objects.filter(team=team).aggregate(total=Coalesce(Sum('amount'), 0))['total'],
        ) if team else 0,
        'team_achievements': list(
            ActivityLog.objects.filter(
                team=team, verb__in=[ActivityLog.Verb.CHALLENGE_COMPLETED, ActivityLog.Verb.BADGE_UNLOCKED]
            ).select_related('actor')[:4]
        ) if team else [],
    }


def team_dashboard(team):
    ledger = PointTransaction.objects.filter(team=team)
    submissions = ActionSubmission.objects.filter(team=team, status=ActionSubmission.Status.APPROVED)
    members = list(
        Membership.objects.filter(team=team).select_related('user').order_by('-role', 'joined_at')
    )
    contributions = dict(ledger.order_by().values_list('user').annotate(total=Sum('amount')))
    for membership in members:
        membership.contribution = contributions.get(membership.user_id, 0)
    month_ago = timezone.now() - timedelta(days=30)
    active_ids = set(ledger.filter(created_at__gte=month_ago).values_list('user_id', flat=True))
    member_ids = {m.user_id for m in members}
    challenge_participations = ChallengeParticipation.objects.filter(team=team)
    joined = challenge_participations.exclude(status=ChallengeParticipation.Status.ABANDONED).count()
    completed = challenge_participations.filter(status=ChallengeParticipation.Status.COMPLETED).count()
    return {
        'points': ledger.aggregate(total=Coalesce(Sum('amount'), 0))['total'],
        'rank': team_rank(team),
        'members': members,
        'member_count': len(members),
        'approved_actions': submissions.count(),
        'co2': approved_co2(submissions),
        'completed_challenges': completed,
        'joined_challenges': joined,
        'challenge_completion_rate': percent(completed, joined),
        'active_members': len(active_ids & member_ids),
        'participation_rate': percent(len(active_ids & member_ids), len(members)),
        'event_participations': EventParticipation.objects.filter(team=team).count(),
        'weekly_points': weekly_series(ledger, 'created_at', 8, 'amount'),
        'categories': category_breakdown(submissions),
        'activities': list(ActivityLog.objects.filter(team=team).select_related('actor')[:10]),
        'goal_progress': percent(ledger.aggregate(total=Coalesce(Sum('amount'), 0))['total'], team.goal_points)
        if team.goal_points else None,
    }


def admin_overview():
    submissions = ActionSubmission.objects.all()
    status_counts = dict(submissions.order_by().values_list('status').annotate(total=Count('pk')))
    users = User.objects.filter(is_active=True)
    total_users = users.count()
    users_in_team = Membership.objects.filter(user__is_active=True).count()
    ledger = PointTransaction.objects.all()
    return {
        'total_users': total_users,
        'total_teams': Team.objects.exclude(status=Team.Status.ARCHIVED).count(),
        'active_challenges': Challenge.objects.filter(status=Challenge.Status.ACTIVE).count(),
        'pending_challenges': Challenge.objects.filter(status=Challenge.Status.PENDING).count(),
        'pending_events': Event.objects.filter(status=Event.Status.PENDING).count(),
        'pending_submissions': status_counts.get(ActionSubmission.Status.PENDING, 0),
        'approved_submissions': status_counts.get(ActionSubmission.Status.APPROVED, 0),
        'rejected_submissions': status_counts.get(ActionSubmission.Status.REJECTED, 0),
        'points_awarded': ledger.filter(amount__gt=0).aggregate(total=Coalesce(Sum('amount'), 0))['total'],
        'points_net': ledger.aggregate(total=Coalesce(Sum('amount'), 0))['total'],
        'co2': approved_co2(submissions),
        'users_in_team': users_in_team,
        'team_participation_rate': percent(users_in_team, total_users),
        'challenge_participants': ChallengeParticipation.objects.exclude(
            status=ChallengeParticipation.Status.ABANDONED).values('user').distinct().count(),
        'challenge_completions': ChallengeParticipation.objects.filter(
            status=ChallengeParticipation.Status.COMPLETED).count(),
        'event_participations': EventParticipation.objects.count(),
        'badge_awards': UserBadge.objects.count(),
        'upcoming_events': Event.objects.filter(status=Event.Status.PUBLISHED, start_at__gte=timezone.now()).count(),
        'weekly_points': weekly_series(ledger.filter(amount__gt=0), 'created_at', 8, 'amount'),
        'weekly_users': weekly_series(User.objects.all(), 'date_joined', 8),
        'status_breakdown': [
            {'label': label, 'value': status_counts.get(value, 0), 'tone': tone}
            for (value, label), tone in zip(ActionSubmission.Status.choices, ['warning', 'success', 'danger'])
        ],
        'categories': category_breakdown(submissions.filter(status=ActionSubmission.Status.APPROVED)),
        'activities': list(ActivityLog.objects.select_related('actor', 'team')[:10]),
        'moderation_queue': list(
            submissions.filter(status=ActionSubmission.Status.PENDING)
            .select_related('user', 'action_type').order_by('created_at')[:5]
        ),
        'top_teams': team_leaderboard()[:5],
    }


def engagement_report(period='month'):
    since = period_start(period)
    submissions = ActionSubmission.objects.filter(status=ActionSubmission.Status.APPROVED)
    new_users = User.objects.all()
    participations = EventParticipation.objects.all()
    if since:
        submissions = submissions.filter(reviewed_at__gte=since)
        new_users = new_users.filter(date_joined__gte=since)
        participations = participations.filter(joined_at__gte=since)
    challenges = (
        Challenge.objects.filter(status__in=[Challenge.Status.ACTIVE, Challenge.Status.COMPLETED])
        .annotate(
            participant_total=Count('participations', filter=~Q(participations__status='abandoned'), distinct=True),
            completed_total=Count('participations', filter=Q(participations__status='completed'), distinct=True),
        )
        .order_by('-start_date')
    )
    challenge_rows = [
        {'challenge': c, 'participants': c.participant_total, 'completed': c.completed_total,
         'rate': percent(c.completed_total, c.participant_total)}
        for c in challenges
    ]
    events = (
        Event.objects.filter(status__in=[Event.Status.PUBLISHED, Event.Status.COMPLETED])
        .annotate(participant_total=Count('participations'))
        .order_by('-start_at')
    )
    event_rows = [
        {'event': e, 'participants': e.participant_total,
         'fill': percent(e.participant_total, e.participation_goal or e.capacity) if (e.participation_goal or e.capacity) else None}
        for e in events
    ]
    return {
        'period': period,
        'approved_actions': submissions.count(),
        'points': submissions.aggregate(total=Coalesce(Sum('points_awarded'), 0))['total'],
        'co2': submissions.aggregate(total=Coalesce(Sum('co2_saved_kg'), ZERO_DECIMAL))['total'],
        'new_users': new_users.count(),
        'event_participations': participations.count(),
        'categories': category_breakdown(submissions),
        'teams': team_leaderboard(period=period),
        'challenges': challenge_rows,
        'events': event_rows,
        'top_users': user_leaderboard(period=period, limit=10),
    }


def landing_stats():
    approved = ActionSubmission.objects.filter(status=ActionSubmission.Status.APPROVED)
    return {
        'users': User.objects.filter(is_active=True).count(),
        'teams': Team.objects.filter(status=Team.Status.ACTIVE).count(),
        'actions': approved.count(),
        'co2': approved_co2(approved),
        'points': PointTransaction.objects.aggregate(total=Coalesce(Sum('amount'), 0))['total'],
        'challenges': Challenge.objects.filter(status=Challenge.Status.ACTIVE).count(),
    }
