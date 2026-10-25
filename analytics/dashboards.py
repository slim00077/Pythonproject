"""Data for the role-specific dashboards and for the administrator control center.

Everything is computed from database records; empty databases produce zeros and empty lists.
"""
from datetime import timedelta

from django.db.models import Count, Q
from django.utils import timezone

from accounts.models import User
from actions.models import ActionSubmission
from challenges.models import Challenge, ChallengeParticipation
from community.models import Event, EventParticipation
from gamification.models import PointTransaction
from organizations.models import Organization
from organizations.services import can_manage, community_summary, workplace_summary
from teams.services import get_user_team

from .services import (
    approved_co2,
    category_breakdown,
    team_leaderboard,
    user_dashboard,
    weekly_series,
)


def suspicious_submissions():
    """Pending declarations that deserve a closer look (computed from the data, never guessed).

    * the action type requires a photo but none was attached;
    * the author declared at least five actions during the last 24 hours.
    """
    day_ago = timezone.now() - timedelta(hours=24)
    bursts = list(
        ActionSubmission.objects.filter(created_at__gte=day_ago).order_by().values('user')
        .annotate(total=Count('pk')).filter(total__gte=5).values_list('user', flat=True)
    )
    pending = ActionSubmission.objects.filter(status=ActionSubmission.Status.PENDING)
    return pending.filter(
        Q(action_type__requires_evidence=True, evidence='') | Q(user__in=bursts)
    ).select_related('user', 'action_type').order_by('created_at')


def cumulative_users(weeks=12):
    """Total registered accounts at the end of each of the last ``weeks`` weeks."""
    weekly = weekly_series(User.objects.all(), 'date_joined', weeks)
    today = timezone.localdate()
    start = today - timedelta(days=today.weekday()) - timedelta(weeks=weeks - 1)
    running = User.objects.filter(date_joined__date__lt=start).count()
    series = []
    for point in weekly:
        running += point['value']
        series.append({'label': point['label'], 'value': running})
    return series


def admin_counters():
    """Extra KPI cards of the control center overview."""
    users = User.objects.filter(is_active=True)
    suspicious = suspicious_submissions()
    now = timezone.now()
    return {
        'students': users.filter(organization_type=User.OrganizationType.STUDENT).count(),
        'employees': users.filter(organization_type=User.OrganizationType.EMPLOYEE).count(),
        'associations': users.filter(organization_type=User.OrganizationType.ASSOCIATION).count(),
        'total_organizations': Organization.objects.filter(is_active=True).count(),
        'suspicious': list(suspicious[:5]),
        'suspicious_total': suspicious.count(),
        'recent_adjustments': PointTransaction.objects.filter(
            reason=PointTransaction.Reason.MANUAL_ADJUSTMENT, created_at__gte=now - timedelta(days=30)
        ).count(),
        'pending_challenge_list': list(
            Challenge.objects.filter(status=Challenge.Status.PENDING).select_related('creator', 'organization')
            .order_by('created_at')[:5]
        ),
        'pending_event_list': list(
            Event.objects.filter(status=Event.Status.PENDING).select_related('organizer', 'organization')
            .order_by('start_at')[:5]
        ),
    }


def admin_statistics():
    """Series for the global statistics page of the control center."""
    submissions = ActionSubmission.objects.all()
    status_counts = dict(submissions.order_by().values_list('status').annotate(total=Count('pk')))
    category_labels = dict(User.OrganizationType.choices)
    registered = dict(
        User.objects.filter(is_active=True).order_by().values_list('organization_type').annotate(total=Count('pk'))
    )
    active_ids = set(PointTransaction.objects.values_list('user_id', flat=True))
    active = dict(
        User.objects.filter(pk__in=active_ids).order_by().values_list('organization_type').annotate(total=Count('pk'))
    )
    per_organization = list(
        Organization.objects.filter(is_active=True).annotate(
            events_total=Count('events', distinct=True),
            actions_total=Count(
                'members__action_submissions',
                filter=Q(members__action_submissions__status=ActionSubmission.Status.APPROVED), distinct=True,
            ),
        ).order_by('-actions_total', '-events_total', 'name')[:8]
    )
    return {
        'user_growth': cumulative_users(12),
        'registered_by_category': [
            {'label': label, 'value': registered.get(value, 0)} for value, label in category_labels.items()
        ],
        'active_by_category': [
            {'label': label, 'value': active.get(value, 0)} for value, label in category_labels.items()
        ],
        'actions_by_category': [
            {'label': row['label'], 'value': row['count']}
            for row in category_breakdown(submissions.filter(status=ActionSubmission.Status.APPROVED))
        ],
        'challenge_completions': weekly_series(
            ChallengeParticipation.objects.filter(status=ChallengeParticipation.Status.COMPLETED),
            'completed_at', 12),
        'participation_over_time': [
            {'label': a['label'], 'value': a['value'] + b['value']}
            for a, b in zip(
                weekly_series(ChallengeParticipation.objects.all(), 'joined_at', 12),
                weekly_series(EventParticipation.objects.all(), 'joined_at', 12),
            )
        ],
        'team_ranking': [{'label': team.name, 'value': team.points} for team in team_leaderboard()[:8]],
        'status_breakdown': [
            {'label': label, 'value': status_counts.get(value, 0), 'tone': tone}
            for (value, label), tone in zip(ActionSubmission.Status.choices, ['warning', 'success', 'danger'])
        ],
        'organization_activity': [
            {'label': org.name, 'value': org.actions_total + org.events_total} for org in per_organization
        ],
    }


def employee_dashboard(user):
    """Corporate dashboard. Colleagues' individual data is never exposed: only team and company aggregates."""
    organization = user.affiliation
    team = get_user_team(user)
    personal = user_dashboard(user)
    data = {
        'organization': organization,
        'team': team,
        'points': personal['points'],
        'approved_count': personal['approved_count'],
        'pending_count': personal['pending_count'],
        'challenges_completed': personal['challenges_completed'],
        'participations': personal['participations'],
        'streak': personal['streak'],
        'badges_count': personal['badges_count'],
        'team_rank': personal['team_rank'],
        'team_points': personal['team_points'],
        'co2': personal['co2'],
        'suggested_challenges': personal['suggested_challenges'],
        'summary': None,
        'org_teams': [],
        'org_challenges': [],
        'campaigns': [],
        'events': [],
        'weekly_points': [],
        'categories': [],
        'achievements': [],
        'my_team_org_rank': None,
    }
    if organization is None:
        return data
    summary = workplace_summary(organization)
    data['summary'] = summary
    org_teams = team_leaderboard(organization=organization)
    data['org_teams'] = org_teams[:6]
    if team is not None:
        data['my_team_org_rank'] = next((row.rank for row in org_teams if row.pk == team.pk), None)
    today = timezone.localdate()
    joined = dict(ChallengeParticipation.objects.filter(user=user).values_list('challenge_id', 'status'))
    org_challenges = list(
        Challenge.objects.filter(organization=organization, status=Challenge.Status.ACTIVE, end_date__gte=today)
        .order_by('end_date')[:4]
    )
    for challenge in org_challenges:
        challenge.my_status = joined.get(challenge.pk)
    data['org_challenges'] = org_challenges
    org_events = Event.objects.filter(
        organization=organization, status=Event.Status.PUBLISHED, end_at__gte=timezone.now()
    )
    data['campaigns'] = list(org_events.filter(kind=Event.Kind.CAMPAIGN).order_by('start_at')[:3])
    data['events'] = list(org_events.filter(kind=Event.Kind.EVENT).order_by('start_at')[:3])
    data['weekly_points'] = weekly_series(summary['ledger'], 'created_at', 8, 'amount')
    data['categories'] = [
        {'label': row['label'], 'value': row['count']} for row in category_breakdown(summary['approved'])
    ]
    data['achievements'] = list(
        ChallengeParticipation.objects.filter(
            team__organization=organization, status=ChallengeParticipation.Status.COMPLETED
        ).order_by().values('team__name', 'challenge__title').annotate(total=Count('pk')).order_by('-total')[:5]
    )
    return data


def association_dashboard(user):
    """Community impact center. Participant details are only shown to the managers of the organization."""
    organization = user.affiliation
    data = {'organization': organization, 'can_manage': False}
    if organization is None:
        return data
    community = community_summary(organization)
    now = timezone.now()
    proposals = dict(community['proposals'].order_by().values_list('status').annotate(total=Count('pk')))
    manager = can_manage(user, organization)
    data.update({
        'can_manage': manager,
        'c': community,
        'upcoming_events': list(community['upcoming'].filter(kind=Event.Kind.EVENT)[:4]),
        'current_campaigns': list(
            community['campaigns'].filter(status=Event.Status.PUBLISHED, start_at__lte=now, end_at__gte=now)
            .annotate(participant_total=Count('participations'))[:4]
        ),
        'upcoming_campaigns': list(
            community['campaigns'].filter(status=Event.Status.PUBLISHED, start_at__gt=now).order_by('start_at')[:3]
        ),
        'proposals': proposals,
        'proposal_total': sum(proposals.values()),
        'members_total': organization.members.filter(is_active=True).count(),
        'weekly_registrations': weekly_series(community['registrations'], 'joined_at', 8),
        'co2': approved_co2(community['campaign_actions']),
        'recent_registrations': list(
            community['registrations'].select_related('user', 'event').order_by('-joined_at')[:5]
        ) if manager else [],
    })
    return data
