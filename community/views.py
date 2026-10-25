from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from core.decorators import any_permission_required
from core.exceptions import BusinessRuleError
from core.permissions import REVIEW_EVENTS

from . import services
from .forms import EventFilterForm, EventForm, EventReviewForm
from .models import Event, EventParticipation


def _visible_event(request, slug):
    event = get_object_or_404(Event.objects.select_related('organizer'), slug=slug)
    if not services.can_view(request.user, event):
        raise Http404
    return event


@login_required
def event_list(request):
    form = EventFilterForm(request.GET or None)
    events = Event.objects.filter(status__in=[Event.Status.PUBLISHED, Event.Status.COMPLETED]).annotate(
        participant_total=Count('participations')
    )
    scope = request.GET.get('scope', '')
    if scope == 'org':
        # « Campagnes et événements » of an employee: only those of the user's own organization.
        events = events.filter(organization_id=request.user.affiliation_id) if request.user.affiliation_id else events.none()
    when = 'upcoming'
    if form.is_valid():
        data = form.cleaned_data
        when = data['when'] or 'upcoming'
        if data['q']:
            events = events.filter(Q(title__icontains=data['q']) | Q(location__icontains=data['q'])
                                   | Q(description__icontains=data['q']))
        for field in ('kind', 'category', 'format'):
            if data[field]:
                events = events.filter(**{field: data[field]})
    now = timezone.now()
    if when == 'upcoming':
        events = events.filter(end_at__gte=now, status=Event.Status.PUBLISHED).order_by('start_at')
    elif when == 'past':
        events = events.filter(Q(end_at__lt=now) | Q(status=Event.Status.COMPLETED)).order_by('-start_at')
    else:
        events = events.order_by('-start_at')
    page = Paginator(events, 9).get_page(request.GET.get('page'))
    joined = set(EventParticipation.objects.filter(user=request.user).values_list('event_id', flat=True))
    campaigns = Event.objects.filter(
        kind=Event.Kind.CAMPAIGN, status=Event.Status.PUBLISHED, start_at__lte=now, end_at__gte=now
    ).annotate(participant_total=Count('participations'))[:3]
    return render(request, 'community/event_list.html', {
        'form': form, 'page': page, 'joined': joined, 'campaigns': campaigns,
        'can_create': services.can_create(request.user), 'scope': scope,
    })


@login_required
def my_events(request):
    participations = EventParticipation.objects.filter(user=request.user).select_related('event').order_by(
        '-event__start_at')
    organized = Event.objects.filter(
        Q(organizer=request.user) | Q(organization_id=request.user.affiliation_id, organization__isnull=False)
        if request.user.can_manage_organization else Q(organizer=request.user)
    ).annotate(
        participant_total=Count('participations')).order_by('-created_at')
    return render(request, 'community/my_events.html', {
        'participations': participations, 'organized': organized, 'can_create': services.can_create(request.user),
    })


@login_required
def event_detail(request, slug):
    event = _visible_event(request, slug)
    participations = event.participations.select_related('user', 'team')
    team_rows = (
        participations.filter(team__isnull=False).values('team__name', 'team__slug')
        .annotate(total=Count('pk')).order_by('-total')[:8]
    )
    return render(request, 'community/event_detail.html', {
        'event': event,
        'participations': participations[:24],
        'participant_total': participations.count(),
        'team_rows': team_rows,
        'is_participant': participations.filter(user=request.user).exists(),
        'is_organizer': services.is_event_manager(request.user, event),
        'can_edit': services.can_edit(request.user, event),
        'can_delete': services.can_delete(request.user, event),
        'can_cancel': services.can_cancel(request.user, event),
        'can_review': services.can_review(request.user),
    })


@login_required
def event_create(request):
    if not services.can_create(request.user):
        raise PermissionDenied
    start = (timezone.localtime() + timedelta(days=7)).replace(hour=10, minute=0, second=0, microsecond=0)
    kind = request.GET.get('kind') if request.GET.get('kind') in Event.Kind.values else Event.Kind.EVENT
    form = EventForm(request.POST or None, initial={
        'start_at': start, 'end_at': start + timedelta(hours=2), 'kind': kind,
    })
    if request.method == 'POST' and form.is_valid():
        event = services.create_event(request.user, form)
        messages.success(request, 'Brouillon enregistré. Soumettez-le à validation pour le publier.')
        return redirect(event)
    return render(request, 'community/event_form.html', {'form': form, 'is_create': True})


@login_required
def event_update(request, slug):
    event = get_object_or_404(Event, slug=slug)
    if not services.can_edit(request.user, event):
        raise PermissionDenied
    form = EventForm(request.POST or None, instance=event)
    if request.method == 'POST' and form.is_valid():
        services.update_event(request.user, event, form)
        messages.success(request, 'Événement mis à jour.')
        return redirect(event)
    return render(request, 'community/event_form.html', {'form': form, 'event': event, 'is_create': False})


@login_required
def event_delete(request, slug):
    event = get_object_or_404(Event, slug=slug)
    if not services.can_delete(request.user, event):
        raise PermissionDenied
    if request.method == 'POST':
        title = event.title
        event.delete()
        messages.success(request, f'« {title} » a été supprimé.')
        return redirect('community:mine')
    return render(request, 'core/confirm_delete.html', {
        'object_label': f'« {event.title} »', 'warning': 'Cette suppression est définitive.',
        'cancel_url': event.get_absolute_url(),
    })


def _run(request, action, success_message, event, *args):
    try:
        action(request.user, event, *args)
    except BusinessRuleError as error:
        messages.error(request, error.message)
    else:
        messages.success(request, success_message)
    return redirect(event)


@login_required
@require_POST
def event_submit(request, slug):
    event = get_object_or_404(Event, slug=slug)
    if not services.is_event_manager(request.user, event):
        raise PermissionDenied
    return _run(request, services.submit_for_review, 'Événement soumis à validation.', event)


@login_required
@require_POST
def event_join(request, slug):
    event = _visible_event(request, slug)
    return _run(request, services.join_event, 'Inscription confirmée. À bientôt !', event)


@login_required
@require_POST
def event_leave(request, slug):
    event = _visible_event(request, slug)
    return _run(request, services.leave_event, 'Votre participation a été annulée.', event)


@login_required
@require_POST
def event_cancel(request, slug):
    event = _visible_event(request, slug)
    return _run(request, services.cancel_event, 'L’événement a été annulé et les participants prévenus.', event,
                request.POST.get('reason', '')[:500])


# --- Back-office ---------------------------------------------------------------

@any_permission_required(REVIEW_EVENTS)
def review_list(request):
    tab = request.GET.get('tab', 'pending')
    tabs = {
        'pending': [Event.Status.PENDING],
        'published': [Event.Status.PUBLISHED],
        'drafts': [Event.Status.DRAFT],
        'closed': [Event.Status.COMPLETED, Event.Status.CANCELLED],
    }
    events = (
        Event.objects.filter(status__in=tabs.get(tab, tabs['pending'])).select_related('organizer')
        .annotate(participant_total=Count('participations')).order_by('start_at')
    )
    counts = {key: Event.objects.filter(status__in=value).count() for key, value in tabs.items()}
    page = Paginator(events, 15).get_page(request.GET.get('page'))
    return render(request, 'community/admin/review_list.html', {'page': page, 'tab': tab, 'counts': counts})


@any_permission_required(REVIEW_EVENTS)
def review_detail(request, slug):
    event = get_object_or_404(Event.objects.select_related('organizer', 'reviewed_by'), slug=slug)
    form = EventReviewForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        decision = request.POST.get('decision')
        notes = form.cleaned_data['notes']
        try:
            if decision == 'publish':
                services.publish_event(request.user, event, notes)
            elif decision == 'reject':
                services.reject_event(request.user, event, notes)
            elif decision == 'complete':
                services.complete_event(request.user, event)
            elif decision == 'cancel':
                services.cancel_event(request.user, event, notes)
            else:
                raise BusinessRuleError('Décision inconnue.')
        except BusinessRuleError as error:
            messages.error(request, error.message)
        else:
            messages.success(request, 'Décision enregistrée.')
            return redirect('community_admin:review_list')
    return render(request, 'community/admin/review_detail.html', {
        'event': event, 'form': form, 'participant_total': event.participations.count(),
    })
