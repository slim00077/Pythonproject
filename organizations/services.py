"""Organization ownership rules and the aggregate statistics shown on organization dashboards.

Every statistic is computed from database records and only exposes
organization-level aggregates: individual colleagues' data stays private.
"""
from datetime import timedelta

from django.db import transaction
from django.db.models import Count, Q, Sum
from django.db.models.functions import Coalesce
from django.utils import timezone

from actions.models import ActionSubmission
from analytics.activity import log_activity
from analytics.models import ActivityLog
from challenges.models import Challenge, ChallengeParticipation
from community.models import Event, EventParticipation
from core.exceptions import BusinessRuleError
from core.utils import percent
from gamification.models import PointTransaction
from teams.models import Team

from .models import Organization


def user_organization(user):
    """The organization an authenticated user belongs to (``None`` otherwise)."""
    if not user.is_authenticated or not user.affiliation_id:
        return None
    return user.affiliation


def can_manage(user, organization):
    """Only an active manager of *this* organization (or an administrator) may edit it."""
    if not (user.is_authenticated and user.is_active and organization is not None):
        return False
    if user.is_superuser:
        return True
    return bool(user.is_org_manager and user.affiliation_id == organization.pk)


def can_view(user, organization):
    """Members of an organization and administrators; never members of other organizations."""
    if not (user.is_authenticated and user.is_active and organization is not None):
        return False
    return user.is_superuser or user.affiliation_id == organization.pk


@transaction.atomic
def create_organization_for(user, form):
    """An association account founds its organization and becomes its first manager."""
    if user.affiliation_id:
        raise BusinessRuleError('Votre compte est déjà rattaché à une organisation.')
    if user.organization_type != user.OrganizationType.ASSOCIATION:
        raise BusinessRuleError('Seuls les comptes de type association peuvent créer une organisation.')
    organization = form.save(commit=False)
    organization.kind = Organization.Kind.ASSOCIATION
    organization.save()
    user.affiliation = organization
    user.is_org_manager = True
    user.save(update_fields=['affiliation', 'is_org_manager'])
    log_activity(user, ActivityLog.Verb.ORGANIZATION_UPDATED, f'Organisation « {organization.name} » créée.',
                 link=organization.get_absolute_url())
    return organization


def update_organization(user, organization, form):
    if not can_manage(user, organization):
        raise BusinessRuleError('Vous n’êtes pas autorisé·e à modifier cette organisation.')
    organization = form.save()
    log_activity(user, ActivityLog.Verb.ORGANIZATION_UPDATED, f'Profil de « {organization.name} » mis à jour.',
                 link=organization.get_absolute_url())
    return organization


# --- Statistics -----------------------------------------------------------------

def member_queryset(organization):
    return organization.members.filter(is_active=True)


def workplace_summary(organization):
    """Aggregate figures for the members of an organization (no individual breakdown)."""
    members = member_queryset(organization)
    member_ids = list(members.values_list('pk', flat=True))
    month_ago = timezone.now() - timedelta(days=30)
    approved = ActionSubmission.objects.filter(user__in=member_ids, status=ActionSubmission.Status.APPROVED)
    ledger = PointTransaction.objects.filter(user__in=member_ids)
    active_ids = set(ledger.filter(created_at__gte=month_ago).values_list('user_id', flat=True))
    challenge_qs = ChallengeParticipation.objects.filter(user__in=member_ids)
    return {
        'member_total': len(member_ids),
        'points': ledger.aggregate(total=Coalesce(Sum('amount'), 0))['total'],
        'approved_actions': approved.count(),
        'active_members': len(active_ids),
        'participation_rate': percent(len(active_ids), len(member_ids)),
        'challenges_completed': challenge_qs.filter(status=ChallengeParticipation.Status.COMPLETED).count(),
        'challenges_joined': challenge_qs.exclude(status=ChallengeParticipation.Status.ABANDONED).count(),
        'teams_total': Team.objects.filter(organization=organization).exclude(status=Team.Status.ARCHIVED).count(),
        'ledger': ledger,
        'approved': approved,
    }


def community_summary(organization):
    """Figures for the community-impact dashboard of an association."""
    events = Event.objects.filter(organization=organization)
    registrations = EventParticipation.objects.filter(event__organization=organization)
    now = timezone.now()
    campaign_actions = ActionSubmission.objects.filter(
        challenge__organization=organization, status=ActionSubmission.Status.APPROVED
    )
    return {
        'campaigns': events.filter(kind=Event.Kind.CAMPAIGN),
        'events_qs': events,
        'campaign_total': events.filter(kind=Event.Kind.CAMPAIGN).count(),
        'event_total': events.filter(kind=Event.Kind.EVENT).count(),
        'registrations': registrations,
        'registration_total': registrations.count(),
        'completed_total': events.filter(Q(status=Event.Status.COMPLETED)).count(),
        'upcoming': events.filter(status=Event.Status.PUBLISHED, end_at__gte=now).order_by('start_at'),
        'draft_total': events.filter(status__in=[Event.Status.DRAFT, Event.Status.PENDING]).count(),
        'proposals': Challenge.objects.filter(organization=organization),
        'campaign_actions': campaign_actions,
        'verified_actions': campaign_actions.count(),
    }
