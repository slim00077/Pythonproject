import math
import time
from datetime import datetime

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from core.context_processors import account_kind
from core.exceptions import BusinessRuleError

from . import ai, rules, services
from .forms import LocationForm

PERIODS = (24, 48, 72)
TONE_COLORS = {'cyan': '#42E8D5', 'blue': '#5B8CFF', 'amber': '#FFC857', 'red': '#FF6B6B', 'muted': '#8C98B5'}


def _period(request):
    try:
        hours = int(request.GET.get('hours', 24))
    except ValueError:
        hours = 24
    return hours if hours in PERIODS else 24


def _orbit_nodes(indicators):
    """Position the indicators on the holographic ring (SVG viewBox 520x520, centre 260,260)."""
    for index, item in enumerate(indicators):
        angle = math.radians(-90 + index * 360 / len(indicators))
        item['cx'] = round(260 + 178 * math.cos(angle), 1)
        item['cy'] = round(260 + 178 * math.sin(angle), 1)
        item['color'] = TONE_COLORS[item['tone']]
    return indicators


@login_required
def dashboard(request):
    location = services.current_location(request)
    hours = _period(request)
    context = {
        'form': LocationForm(initial={'query': location['name']}), 'location': location, 'hours': hours,
        'periods': PERIODS, 'ai_enabled': ai.is_configured(),
    }
    try:
        snapshot, meta = services.get_snapshot(location)
    except services.EnvironmentUnavailable as exc:
        context['error'] = str(exc) or 'Données environnementales indisponibles.'
        return render(request, 'ecopulse/dashboard.html', context)
    now_ts = int(time.time())
    assessment = rules.evaluate_period(snapshot, now_ts, hours)
    _orbit_nodes(assessment['indicators'])
    events = services.events_exposure(request.user, snapshot)
    age = services.snapshot_age_minutes(snapshot)
    context.update(
        snapshot=snapshot, meta=meta, assessment=assessment, advice=rules.rule_based_advice(assessment),
        events=events, age_minutes=age, is_stale=meta['origin'] == 'stale' or age > 60,
        period_start=rules.local_time_text(snapshot, assessment['start_ts']),
        period_end=rules.local_time_text(snapshot, assessment['end_ts']),
        charts=rules.chart_series(snapshot, now_ts, hours),
        fetched_text=rules.local_time_text(snapshot, int(datetime.fromisoformat(snapshot['fetched_at']).timestamp())),
        coverage_hours=assessment['hours'],
    )
    return render(request, 'ecopulse/dashboard.html', context)


@login_required
@require_POST
def set_location(request):
    form = LocationForm(request.POST)
    if form.is_valid():
        data = form.cleaned_data
        try:
            location = services.resolve_location(data['query'], data['latitude'], data['longitude'])
        except BusinessRuleError as exc:
            messages.error(request, exc.message)
        else:
            request.session[services.SESSION_LOCATION] = location
            messages.success(request, f'Lieu mis à jour : {location["name"]}.')
    else:
        for errors in form.errors.values():
            for error in errors:
                messages.error(request, error)
    return redirect('ecopulse:dashboard')


@login_required
@require_POST
def refresh(request):
    try:
        services.request_refresh(request.user, services.current_location(request))
    except BusinessRuleError as exc:
        messages.warning(request, exc.message)
    except services.EnvironmentUnavailable as exc:
        messages.error(request, str(exc) or 'Actualisation impossible.')
    else:
        messages.success(request, 'Données actualisées.')
    return redirect('ecopulse:dashboard')


@login_required
@require_POST
def ai_analysis(request):
    """JSON endpoint called by the dashboard after the page has rendered (loading state in the browser)."""
    location = services.current_location(request)
    try:
        snapshot, _meta = services.get_snapshot(location)
    except services.EnvironmentUnavailable as exc:
        return JsonResponse({'ok': False, 'error': str(exc) or 'Données indisponibles.'}, status=503)
    hours = _period(request)
    assessment = rules.evaluate_period(snapshot, int(time.time()), hours)
    if assessment['outdoor'] == 'unknown':
        return JsonResponse({'ok': False, 'error': 'Données insuffisantes pour une analyse fiable.'}, status=422)
    events = services.events_exposure(request.user, snapshot)
    try:
        result = services.run_ai_analysis(
            request.user, request.session, snapshot, assessment, events, account_kind(request.user))
    except ai.AIError as exc:
        return JsonResponse({'ok': False, 'error': str(exc)}, status=502)
    return JsonResponse({'ok': True, **result})


@login_required
@require_POST
def save_proposal(request):
    try:
        index = int(request.POST.get('index', ''))
    except ValueError:
        return JsonResponse({'ok': False, 'error': 'Proposition invalide.'}, status=400)
    try:
        challenge = services.save_proposal(
            request.user, request.session, request.POST.get('batch', ''), index, request.POST.get('mode', ''))
    except BusinessRuleError as exc:
        return JsonResponse({'ok': False, 'error': exc.message}, status=400)
    label = 'soumis à validation' if challenge.status == challenge.Status.PENDING else 'enregistré comme brouillon'
    return JsonResponse({'ok': True, 'url': challenge.get_absolute_url(), 'message': f'Défi {label}.'})
