from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from analytics import services as analytics
from analytics.activity import log_activity
from analytics.models import ActivityLog
from community.models import Event, EventParticipation
from core.decorators import superuser_required
from core.exceptions import BusinessRuleError
from challenges.models import Challenge

from . import services
from .decorators import org_manager_required
from .forms import OrganizationAdminForm, OrganizationProfileForm, ParticipantFilterForm
from .models import Organization

ORGANIZATION_VERBS = [
    ActivityLog.Verb.EVENT_CREATED, ActivityLog.Verb.EVENT_PUBLISHED, ActivityLog.Verb.EVENT_STATUS,
    ActivityLog.Verb.CHALLENGE_CREATED, ActivityLog.Verb.CHALLENGE_SUBMITTED, ActivityLog.Verb.CHALLENGE_PUBLISHED,
    ActivityLog.Verb.CHALLENGE_REJECTED, ActivityLog.Verb.ORGANIZATION_UPDATED,
]


# --- Member-facing pages (company or association) ------------------------------------

@login_required
def detail(request):
    """The organization the signed-in user belongs to (« Mon entreprise » / « Profil de l’organisation »)."""
    organization = services.user_organization(request.user)
    if organization is None:
        return render(request, 'organizations/detail.html', {'organization': None})
    summary = services.workplace_summary(organization)
    community = services.community_summary(organization)
    return render(request, 'organizations/detail.html', {
        'organization': organization,
        'can_manage': services.can_manage(request.user, organization),
        'summary': summary,
        'community': community,
        'upcoming': community['upcoming'][:4],
        'weekly_points': analytics.weekly_series(summary['ledger'], 'created_at', 8, 'amount'),
        'is_association_view': request.user.organization_type == request.user.OrganizationType.ASSOCIATION,
    })


@login_required
def create(request):
    user = request.user
    if user.affiliation_id:
        return redirect('organizations:detail')
    if user.organization_type != user.OrganizationType.ASSOCIATION:
        raise PermissionDenied
    form = OrganizationProfileForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        try:
            services.create_organization_for(user, form)
        except BusinessRuleError as error:
            messages.error(request, error.message)
        else:
            messages.success(request, 'Votre organisation est créée : vous en êtes le gestionnaire.')
            return redirect('organizations:detail')
    return render(request, 'organizations/form.html', {'form': form, 'is_create': True})


@org_manager_required
def settings_view(request, organization):
    form = OrganizationProfileForm(request.POST or None, request.FILES or None, instance=organization)
    if request.method == 'POST' and form.is_valid():
        services.update_organization(request.user, organization, form)
        messages.success(request, 'Profil de l’organisation mis à jour.')
        return redirect('organizations:detail')
    return render(request, 'organizations/form.html', {
        'form': form, 'organization': organization, 'is_create': False,
        'colleagues': organization.members.filter(is_active=True).order_by('first_name', 'username'),
    })


# --- Association manager workspace ------------------------------------------------------

def _event_list(request, organization, kind, template_context):
    status = request.GET.get('status', '')
    events = Event.objects.filter(organization=organization, kind=kind).annotate(
        participant_total=Count('participations')).order_by('-start_at')
    if status in Event.Status.values:
        events = events.filter(status=status)
    page = Paginator(events, 12).get_page(request.GET.get('page'))
    return render(request, 'organizations/event_list.html', {
        'page': page, 'status': status, 'statuses': Event.Status.choices, 'organization': organization,
        **template_context,
    })


@org_manager_required
def campaigns(request, organization):
    return _event_list(request, organization, Event.Kind.CAMPAIGN, {
        'kind': 'campaign', 'title': 'Mes campagnes', 'singular': 'campagne', 'icon': 'megaphone',
        'sub': 'Collectes, nettoyages, plantations… vos campagnes sont validées par l’équipe EcoTeams avant publication.',
    })


@org_manager_required
def events(request, organization):
    return _event_list(request, organization, Event.Kind.EVENT, {
        'kind': 'event', 'title': 'Événements écologiques', 'singular': 'événement', 'icon': 'calendar',
        'sub': 'Ateliers, conférences et rencontres ouverts aux inscriptions de la communauté.',
    })


@org_manager_required
def proposals(request, organization):
    status = request.GET.get('status', '')
    challenges = Challenge.objects.filter(organization=organization).annotate(
        participant_total=Count('participations', filter=~Q(participations__status='abandoned'))
    ).order_by('-created_at')
    if status in Challenge.Status.values:
        challenges = challenges.filter(status=status)
    page = Paginator(challenges, 12).get_page(request.GET.get('page'))
    counts = dict(Challenge.objects.filter(organization=organization).order_by().values_list('status').annotate(
        total=Count('pk')))
    return render(request, 'organizations/proposals.html', {
        'organization': organization, 'page': page, 'status': status, 'statuses': Challenge.Status.choices,
        'counts': counts,
    })


@org_manager_required
def participants(request, organization):
    form = ParticipantFilterForm(request.GET or None, organization=organization)
    registrations = EventParticipation.objects.filter(event__organization=organization).select_related(
        'user', 'event', 'team').order_by('-joined_at')
    if form.is_valid():
        data = form.cleaned_data
        if data['event']:
            registrations = registrations.filter(event=data['event'])
        if data['q']:
            registrations = registrations.filter(
                Q(user__username__icontains=data['q']) | Q(user__first_name__icontains=data['q'])
                | Q(user__last_name__icontains=data['q']))
    page = Paginator(registrations, 20).get_page(request.GET.get('page'))
    unique = EventParticipation.objects.filter(event__organization=organization).values('user').distinct().count()
    return render(request, 'organizations/participants.html', {
        'organization': organization, 'form': form, 'page': page, 'unique_participants': unique,
    })


@org_manager_required
def impact(request, organization):
    community = services.community_summary(organization)
    registrations = community['registrations']
    per_event = list(
        Event.objects.filter(organization=organization).annotate(total=Count('participations'))
        .filter(total__gt=0).order_by('-total')[:8]
    )
    categories = analytics.category_breakdown(community['campaign_actions'])
    event_categories = [
        {'label': label, 'value': community['events_qs'].filter(category=value).count()}
        for value, label in Event._meta.get_field('category').choices
    ]
    return render(request, 'organizations/impact.html', {
        'organization': organization, 'c': community,
        'co2': analytics.approved_co2(community['campaign_actions']),
        'weekly_registrations': analytics.weekly_series(registrations, 'joined_at', 12),
        'per_event_chart': [{'label': e.title, 'value': e.total} for e in per_event],
        'action_categories': [{'label': row['label'], 'value': row['count']} for row in categories],
        'event_categories': event_categories,
    })


@org_manager_required
def history(request, organization):
    logs = ActivityLog.objects.filter(
        actor__affiliation=organization, verb__in=ORGANIZATION_VERBS).select_related('actor').order_by('-created_at')
    page = Paginator(logs, 20).get_page(request.GET.get('page'))
    return render(request, 'organizations/history.html', {'organization': organization, 'page': page})


# --- Global control center ----------------------------------------------------------------

@superuser_required
def admin_list(request):
    query = request.GET.get('q', '').strip()
    kind = request.GET.get('kind', '')
    organizations = Organization.objects.annotate(
        member_total=Count('members', distinct=True), event_total=Count('events', distinct=True),
        challenge_total=Count('challenges', distinct=True), team_total=Count('teams', distinct=True),
    )
    if query:
        organizations = organizations.filter(Q(name__icontains=query) | Q(city__icontains=query))
    if kind in Organization.Kind.values:
        organizations = organizations.filter(kind=kind)
    page = Paginator(organizations.order_by('name'), 20).get_page(request.GET.get('page'))
    return render(request, 'organizations/admin/list.html', {
        'page': page, 'query': query, 'kind': kind, 'kinds': Organization.Kind.choices,
    })


@superuser_required
def admin_form(request, pk=None):
    organization = get_object_or_404(Organization, pk=pk) if pk else None
    form = OrganizationAdminForm(request.POST or None, request.FILES or None, instance=organization)
    if request.method == 'POST' and form.is_valid():
        saved = form.save()
        log_activity(request.user, ActivityLog.Verb.ORGANIZATION_UPDATED,
                     f'Organisation « {saved.name} » {"créée" if organization is None else "modifiée"}.', team=None)
        messages.success(request, f'Organisation « {saved.name} » enregistrée.')
        return redirect('organizations:admin_list')
    members = organization.members.order_by('username') if organization else []
    return render(request, 'organizations/admin/form.html', {'form': form, 'organization': organization, 'members': members})


@superuser_required
def admin_delete(request, pk):
    organization = get_object_or_404(Organization, pk=pk)
    if request.method == 'POST':
        name = organization.name
        organization.delete()
        messages.success(request, f'Organisation « {name} » supprimée. Ses membres ne sont plus rattachés.')
        return redirect('organizations:admin_list')
    return render(request, 'core/confirm_delete.html', {
        'object_label': f'l’organisation « {organization.name} »',
        'warning': f'{organization.members.count()} compte(s) seront détachés de cette organisation ; '
                   'leurs événements et défis sont conservés.',
        'cancel_url': reverse('organizations:admin_list'),
    })
