"""Business rules of EcoPulse: locations, cached data retrieval, rate limits, AI orchestration, drafts."""
import hashlib
import json
import logging
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta

from django.conf import settings
from django.core.cache import cache
from django.db.models import Q
from django.utils import timezone

from challenges import services as challenge_services
from challenges.forms import ChallengeForm
from community.models import Event
from core.exceptions import BusinessRuleError

from . import ai, providers, rules

logger = logging.getLogger('ecoteams.ecopulse')

SESSION_LOCATION = 'ecopulse_location'
SESSION_PROPOSALS = 'ecopulse_proposals'
STALE_SECONDS = 6 * 3600
PARTIAL_CACHE_SECONDS = 120
FORCE_REFRESH_COOLDOWN = 60


class EnvironmentUnavailable(Exception):
    """No usable environmental data (live or cached); the message is safe to display."""


# --- Locations -------------------------------------------------------------------------------


def _round_key(location):
    return f'{location["lat"]:.2f}:{location["lon"]:.2f}'


def validate_coordinates(lat, lon):
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise BusinessRuleError('Coordonnées invalides (latitude -90 à 90, longitude -180 à 180).')


def resolve_location(query='', lat=None, lon=None):
    """Turn the settings form into ``{name, lat, lon}`` (geocoding only when coordinates are absent)."""
    query = (query or '').strip()
    if lat is not None and lon is not None:
        validate_coordinates(lat, lon)
        return {'name': query or f'{lat:.2f}, {lon:.2f}', 'lat': float(lat), 'lon': float(lon)}
    if not query:
        raise BusinessRuleError('Indiquez une ville ou des coordonnées.')
    cache_key = 'ecopulse:geo:' + hashlib.sha1(query.lower().encode()).hexdigest()
    place = cache.get(cache_key)
    if place is None:
        _spend_provider_calls(1)
        try:
            results = providers.geocode(query)
        except providers.ProviderError as exc:
            raise BusinessRuleError(str(exc)) from exc
        if not results:
            raise BusinessRuleError(f'Aucun lieu trouvé pour « {query} ».')
        first = results[0]
        parts = [first.get('name') or query, first.get('admin1'), first.get('country')]
        place = {'name': ', '.join(dict.fromkeys(p for p in parts if p)),
                 'lat': float(first['latitude']), 'lon': float(first['longitude'])}
        validate_coordinates(place['lat'], place['lon'])
        cache.set(cache_key, place, 7 * 86400)
    return place


def current_location(request):
    saved = request.session.get(SESSION_LOCATION)
    if isinstance(saved, dict) and {'name', 'lat', 'lon'} <= saved.keys():
        return saved
    user = request.user
    city = user.affiliation.city if user.affiliation_id and user.affiliation.city else ''
    if city:
        try:
            return resolve_location(city)
        except BusinessRuleError:
            logger.info('EcoPulse: organization city %r could not be resolved, using default', city)
    return dict(settings.ECOPULSE_DEFAULT_LOCATION)


# --- Rate limiting and cache -------------------------------------------------------------------


def _spend_provider_calls(count):
    """Global protection of the free Open-Meteo quota (calls per hour for the whole site)."""
    key = f'ecopulse:budget:{int(time.time() // 3600)}'
    cache.add(key, 0, 3700)
    try:
        used = cache.incr(key, count)
    except ValueError:
        used = count
    if used > settings.ECOPULSE_MAX_PROVIDER_CALLS_PER_HOUR:
        raise BusinessRuleError('Quota horaire de requêtes météo atteint : réessayez dans quelques minutes.')


def _hit_limit(key, limit, window_seconds):
    """Return True if ``key`` already reached ``limit`` hits in the window (and register this hit)."""
    cache.add(key, 0, window_seconds)
    try:
        count = cache.incr(key)
    except ValueError:
        count = 1
    return count > limit


def _fetch_live(location):
    days = settings.ECOPULSE_FORECAST_DAYS
    _spend_provider_calls(2)
    errors = {}
    results = {}

    def run(name, func):
        try:
            results[name] = func(location['lat'], location['lon'], days)
        except providers.ProviderError as exc:
            errors[name] = str(exc)

    with ThreadPoolExecutor(max_workers=2) as pool:
        for future in [pool.submit(run, 'forecast', providers.fetch_forecast),
                       pool.submit(run, 'air', providers.fetch_air_quality)]:
            future.result()
    if not results:
        raise EnvironmentUnavailable(' '.join(dict.fromkeys(errors.values())))
    try:
        snapshot = rules.build_snapshot(location, results.get('forecast'), results.get('air'), timezone.now())
    except ValueError as exc:
        raise EnvironmentUnavailable('Les données reçues sont inutilisables.') from exc
    snapshot['errors'] = list(dict.fromkeys(errors.values()))
    return snapshot


def get_snapshot(location, force=False):
    """Return ``(snapshot, meta)``; meta says whether data is live, cached or stale and why."""
    key = f'ecopulse:snap:{_round_key(location)}'
    if not force:
        cached = cache.get(key)
        if cached is not None:
            return cached, {'origin': 'cache', 'error': ''}
    try:
        snapshot = _fetch_live(location)
    except (EnvironmentUnavailable, BusinessRuleError) as exc:
        stale = cache.get(f'ecopulse:stale:{_round_key(location)}')
        if stale is not None:
            return stale, {'origin': 'stale', 'error': str(exc) or 'Service météo indisponible.'}
        if isinstance(exc, EnvironmentUnavailable):
            raise
        raise EnvironmentUnavailable(str(exc)) from exc
    ttl = PARTIAL_CACHE_SECONDS if snapshot['missing_services'] else settings.ECOPULSE_CACHE_SECONDS
    cache.set(key, snapshot, ttl)
    cache.set(f'ecopulse:stale:{_round_key(location)}', snapshot, STALE_SECONDS)
    return snapshot, {'origin': 'live', 'error': ''}


def request_refresh(user, location):
    """Forced refresh, limited to once per minute and per user."""
    if _hit_limit(f'ecopulse:refresh:{user.pk}', 1, FORCE_REFRESH_COOLDOWN):
        raise BusinessRuleError('Actualisation déjà demandée à l’instant : patientez une minute.')
    return get_snapshot(location, force=True)


def snapshot_age_minutes(snapshot):
    fetched = datetime.fromisoformat(snapshot['fetched_at'])
    return max(0, int((timezone.now() - fetched).total_seconds() // 60))


# --- Events ------------------------------------------------------------------------------------


def events_exposure(user, snapshot):
    """Upcoming on-site events of the user (organizer or own organization) covered by the forecast."""
    now = timezone.now()
    horizon = now + timedelta(seconds=rules.coverage_end(snapshot) - int(now.timestamp()))
    queryset = Event.objects.filter(
        status=Event.Status.PUBLISHED, start_at__gte=now, start_at__lt=horizon,
        format__in=[Event.Format.ON_SITE, Event.Format.HYBRID],
    )
    scope = Q(organizer=user)
    if user.affiliation_id:
        scope |= Q(organization_id=user.affiliation_id)
    rows = []
    for event in queryset.filter(scope).distinct().order_by('start_at')[:8]:
        exposure = rules.event_exposure(snapshot, int(event.start_at.timestamp()), int(event.end_at.timestamp()))
        if not exposure.get('covered'):
            continue
        rows.append({
            'event': event, 'title': event.title, 'outdoor': exposure['outdoor'],
            'level_label': exposure['overall_label'], 'tone': exposure['overall_tone'],
            'start_text': rules.local_time_text(snapshot, int(event.start_at.timestamp())),
            'triggers': exposure['triggers'], 'partial': exposure['partially_covered'],
            'needs_review': exposure['outdoor'] == 'unsuitable',
            'outdoor_label': exposure['outdoor_label'],
        })
    return rows


# --- AI orchestration --------------------------------------------------------------------------


def run_ai_analysis(user, request_session, snapshot, assessment, events, account_kind):
    """Rate-limited, cached AI analysis. Stores the proposals server-side (session) for later review."""
    location_name = snapshot['location']['name']
    context = ai.build_context(snapshot, assessment, location_name, events, account_kind)
    context_key = 'ecopulse:ai:' + hashlib.sha1(
        json.dumps(context, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
    cached = cache.get(context_key)
    if cached is not None:
        result, elapsed, from_cache = cached, 0.0, True
    else:
        if _hit_limit(f'ecopulse:ai:user:{user.pk}', settings.ECOPULSE_AI_MAX_PER_HOUR, 3600):
            raise ai.AIError('Limite de demandes d’analyse IA atteinte pour cette heure. Réessayez plus tard.')
        result, elapsed = ai.analyze(context, assessment['outdoor'])
        cache.set(context_key, result, settings.ECOPULSE_AI_CACHE_SECONDS)
        from_cache = False
    batch = {
        'id': uuid.uuid4().hex, 'location': location_name, 'generated_at': timezone.now().isoformat(),
        'items': [{**proposal, 'saved_slug': ''} for proposal in result['proposals']],
    }
    request_session[SESSION_PROPOSALS] = batch
    return {**result, 'batch_id': batch['id'], 'elapsed': round(elapsed, 2), 'from_cache': from_cache,
            'model': settings.ECOPULSE_AI_MODEL}


# --- Saving a proposal as a regular challenge ------------------------------------------------------


def save_proposal(user, session, batch_id, index, mode):
    """Create a draft (or a pending challenge) from a proposal held server-side.

    Uses the existing challenge workflow: the challenge is a private draft of
    the user; ``pending`` goes through ``submit_for_review``. Nothing is
    published and no point is awarded here — reviewers decide (and set the
    reward) in the usual approval queue.
    """
    batch = session.get(SESSION_PROPOSALS)
    if not batch or batch.get('id') != batch_id:
        raise BusinessRuleError('Cette proposition a expiré : relancez l’analyse.')
    try:
        item = batch['items'][index]
    except (IndexError, TypeError):
        raise BusinessRuleError('Proposition introuvable.')
    if item.get('saved_slug'):
        raise BusinessRuleError('Cette proposition a déjà été enregistrée.')
    if mode not in ('draft', 'pending'):
        raise BusinessRuleError('Action inconnue.')
    today = timezone.localdate()
    note = (f'\n\nProposition générée par EcoPulse IA à partir des conditions environnementales de '
            f'{batch["location"]} ({today:%d/%m/%Y}). Relecture humaine requise avant publication.')
    form = ChallengeForm(data={
        'title': item['title'], 'category': item['category'], 'difficulty': item['difficulty'],
        'description': item['description'] + note, 'instructions': '\n'.join(item['instructions']),
        'start_date': today.isoformat(), 'end_date': (today + timedelta(days=item['duration_days'] + 7)).isoformat(),
        'duration_days': item['duration_days'], 'required_actions': item['required_actions'],
        'reward_points': 0,
    })
    if not form.is_valid():
        raise BusinessRuleError('La proposition ne respecte pas les règles des défis : modifiez-la manuellement.')
    challenge = challenge_services.create_challenge(user, form)
    if mode == 'pending':
        challenge_services.submit_for_review(user, challenge)
    item['saved_slug'] = challenge.slug
    session[SESSION_PROPOSALS] = batch
    session.modified = True
    return challenge
