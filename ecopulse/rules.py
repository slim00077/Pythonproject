"""Deterministic environmental rules of EcoPulse.

Everything that is a measurement or a threshold decision lives here — the
language model never computes or invents these values. Thresholds are
*indicative classification bands for choosing eco-activities*, adapted from
public references (WHO UV index bands, European Air Quality Index bands, WHO
PM2.5 24 h guideline, common wind/heat comfort scales). They are NOT official
warning criteria; they can be overridden with ``ECOPULSE_THRESHOLDS`` in the
settings.

A threshold list ``[a, b, c]`` means: value < a -> level 0, a <= value < b ->
level 1, b <= value < c -> level 2, value >= c -> level 3 (lower bounds are
inclusive). Cold thresholds are symmetrical: value <= a -> level 1, etc.
"""
import calendar
from datetime import datetime, timezone as dt_timezone

from django.conf import settings

LEVELS = {
    0: {'label': 'Favorable', 'tone': 'cyan'},
    1: {'label': 'Modéré', 'tone': 'blue'},
    2: {'label': 'Élevé', 'tone': 'amber'},
    3: {'label': 'Critique', 'tone': 'red'},
}

DEFAULT_THRESHOLDS = {
    'heat': [30, 35, 40],           # °C, apparent temperature (max over the period)
    'cold': [5, 0, -5],             # °C, apparent temperature (min over the period), value <= bound
    'precipitation': [2, 5, 10],    # mm per hour (max over the period)
    'wind': [40, 60, 80],           # km/h gusts (max over the period)
    'uv': [3, 6, 8],                # UV index (max): WHO bands moderate / high / very high
    'aqi': [40, 60, 80],            # European AQI (max): EEA bands moderate / poor / very poor
    'pm25': [15, 25, 50],           # µg/m³ (max): WHO 24 h guideline 15, EU daily reference 25
}

# Plausibility ranges: anything outside is treated as missing, never displayed as a measurement.
VALID_RANGES = {
    'temp': (-60, 60), 'feels': (-80, 70), 'pop': (0, 100), 'precip': (0, 300),
    'gust': (0, 400), 'aqi': (0, 500), 'pm25': (0, 1000), 'uv': (0, 20),
}

INDICATORS = [
    {'key': 'temperature', 'label': 'Température ressentie', 'unit': '°C', 'field': 'feels', 'icon': 'sun'},
    {'key': 'precipitation', 'label': 'Précipitations', 'unit': 'mm/h', 'field': 'precip', 'icon': 'droplet'},
    {'key': 'wind', 'label': 'Rafales de vent', 'unit': 'km/h', 'field': 'gust', 'icon': 'wind'},
    {'key': 'uv', 'label': 'Indice UV', 'unit': '', 'field': 'uv', 'icon': 'zap'},
    {'key': 'aqi', 'label': 'Qualité de l’air (AQI européen)', 'unit': '', 'field': 'aqi', 'icon': 'cloud'},
    {'key': 'pm25', 'label': 'Particules fines PM2,5', 'unit': 'µg/m³', 'field': 'pm25', 'icon': 'activity'},
]

OUTDOOR_LABELS = {
    'suitable': 'Conditions favorables aux activités extérieures',
    'caution': 'Activités extérieures possibles avec précautions',
    'unsuitable': 'Activités extérieures déconseillées',
    'unknown': 'Évaluation impossible (données manquantes)',
}


def thresholds():
    merged = {key: list(value) for key, value in DEFAULT_THRESHOLDS.items()}
    for key, value in (getattr(settings, 'ECOPULSE_THRESHOLDS', None) or {}).items():
        if key in merged and len(value) == 3:
            merged[key] = list(value)
    return merged


def level_up(value, bounds):
    """Number of (inclusive) lower bounds reached by ``value``."""
    return sum(1 for bound in bounds if value >= bound)


def level_down(value, bounds):
    return sum(1 for bound in bounds if value <= bound)


def clean_number(value, field):
    """Return a float if ``value`` is a plausible measurement, else None."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    if value != value or value in (float('inf'), float('-inf')):  # NaN / inf
        return None
    low, high = VALID_RANGES[field]
    return float(value) if low <= value <= high else None


# --- Snapshot construction -------------------------------------------------------------------


def _epoch(local_text, utc_offset):
    """Epoch seconds of an Open-Meteo local time string such as ``2026-10-25T14:00``."""
    try:
        naive = datetime.strptime(local_text[:16], '%Y-%m-%dT%H:%M')
    except (TypeError, ValueError):
        return None
    return calendar.timegm(naive.timetuple()) - int(utc_offset)


def _series(block, name, count):
    values = (block or {}).get(name)
    if not isinstance(values, list):
        return [None] * count
    return (values + [None] * count)[:count]


FORECAST_FIELDS = {'temperature_2m': 'temp', 'apparent_temperature': 'feels', 'precipitation_probability': 'pop',
                   'precipitation': 'precip', 'wind_gusts_10m': 'gust'}
AIR_FIELDS = {'european_aqi': 'aqi', 'pm2_5': 'pm25', 'uv_index': 'uv'}


def build_snapshot(location, forecast, air, fetched_at):
    """Validate the two provider payloads and merge them into one hourly table.

    ``forecast`` or ``air`` may be None when only one service answered; the
    matching indicators are then simply unavailable. Raises ValueError if no
    usable hourly data is left at all.
    """
    rows = {}
    warnings = []
    offsets = []
    sources = []
    for payload, mapping, source in (
        (forecast, FORECAST_FIELDS, 'Open-Meteo Forecast'),
        (air, AIR_FIELDS, 'Open-Meteo Air Quality'),
    ):
        if payload is None:
            continue
        hourly = payload.get('hourly') if isinstance(payload.get('hourly'), dict) else {}
        times = hourly.get('time')
        if not isinstance(times, list) or not times:
            warnings.append(f'{source} : aucune prévision horaire reçue.')
            continue
        offset = payload.get('utc_offset_seconds')
        offset = offset if isinstance(offset, int) and not isinstance(offset, bool) else 0
        offsets.append(offset)
        sources.append(source)
        for api_name, field in mapping.items():
            for text, raw in zip(times, _series(hourly, api_name, len(times))):
                ts = _epoch(text, offset)
                if ts is None:
                    continue
                cleaned = clean_number(raw, field)
                if raw is not None and cleaned is None:
                    warnings.append(f'Valeur « {field} » invalide ignorée.')
                rows.setdefault(ts, {})[field] = cleaned
    if not rows:
        raise ValueError('Aucune donnée horaire exploitable.')
    fields = list(VALID_RANGES)
    hours = [{'ts': ts, **{f: rows[ts].get(f) for f in fields}} for ts in sorted(rows)]
    current = {}
    for payload, mapping in (
        (forecast, {'temperature_2m': 'temp', 'apparent_temperature': 'feels'}),
        (air, AIR_FIELDS),
    ):
        block = payload.get('current') if payload and isinstance(payload.get('current'), dict) else {}
        for api_name, field in mapping.items():
            current[field] = clean_number(block.get(api_name), field)
    return {
        'location': location, 'fetched_at': fetched_at.isoformat(), 'utc_offset': offsets[0] if offsets else 0,
        'timezone': (forecast or air or {}).get('timezone', ''), 'sources': sources,
        'hours': hours, 'current': current, 'warnings': list(dict.fromkeys(warnings))[:5],
        'missing_services': [name for name, payload in (('prévisions météo', forecast), ('qualité de l’air', air))
                             if payload is None],
    }


# --- Evaluation ------------------------------------------------------------------------------


def _indicator_level(key, values, minimum=None):
    bounds = thresholds()
    if key == 'temperature':
        return max(level_up(max(values), bounds['heat']), level_down(minimum, bounds['cold']))
    return level_up(max(values), bounds[key])


def evaluate(snapshot, start_ts, end_ts):
    """Classify the conditions of ``snapshot`` between two epoch timestamps (end exclusive)."""
    window = [h for h in snapshot['hours'] if start_ts <= h['ts'] < end_ts]
    indicators = []
    for spec in INDICATORS:
        values = [h[spec['field']] for h in window if h.get(spec['field']) is not None]
        item = {**spec, 'available': bool(values), 'samples': len(values), 'hours': len(window)}
        if not values:
            item.update(value=None, level=None, level_label='Donnée indisponible', tone='muted', minimum=None)
        else:
            minimum = min(values) if spec['key'] == 'temperature' else None
            level = _indicator_level(spec['key'], values, minimum)
            item.update(value=max(values), minimum=minimum, level=level, level_label=LEVELS[level]['label'],
                        tone=LEVELS[level]['tone'])
        item['partial'] = bool(values) and len(values) < len(window)
        indicators.append(item)
    levels = [i['level'] for i in indicators if i['level'] is not None]
    overall = max(levels) if levels else None
    if overall is None:
        outdoor = 'unknown'
    elif overall >= 2:
        outdoor = 'unsuitable'
    elif overall == 1:
        outdoor = 'caution'
    else:
        outdoor = 'suitable'
    return {
        'start_ts': start_ts, 'end_ts': end_ts, 'hours': len(window), 'indicators': indicators,
        'overall_level': overall,
        'overall_label': LEVELS[overall]['label'] if overall is not None else 'Indisponible',
        'overall_tone': LEVELS[overall]['tone'] if overall is not None else 'muted',
        'outdoor': outdoor, 'outdoor_label': OUTDOOR_LABELS[outdoor],
        'triggers': [i for i in indicators if i['level'] is not None and i['level'] >= 2],
    }


def hour_floor(ts):
    return ts - (ts % 3600)


def evaluate_period(snapshot, now_ts, hours):
    """Evaluation from the current hour for ``hours`` hours."""
    start = hour_floor(now_ts)
    return evaluate(snapshot, start, start + hours * 3600)


def coverage_end(snapshot):
    return snapshot['hours'][-1]['ts'] + 3600


def event_exposure(snapshot, start_ts, end_ts):
    """Assess one scheduled event, or say that the forecast does not cover it."""
    if end_ts <= snapshot['hours'][0]['ts'] or start_ts >= coverage_end(snapshot):
        return {'covered': False}
    start = hour_floor(start_ts)
    end = end_ts if end_ts % 3600 == 0 else hour_floor(end_ts) + 3600
    result = evaluate(snapshot, start, max(end, start + 3600))
    result['covered'] = result['hours'] > 0
    result['partially_covered'] = end_ts > coverage_end(snapshot)
    return result


def local_time_text(snapshot, ts, fmt='%d/%m %H:%M'):
    return datetime.fromtimestamp(ts + snapshot['utc_offset'], dt_timezone.utc).strftime(fmt)


def chart_series(snapshot, now_ts, hours):
    """Hourly series for the dashboard charts (labels in the location's local time)."""
    start = hour_floor(now_ts)
    out = {'temperature': [], 'precipitation': [], 'aqi': [], 'wind': []}
    for h in snapshot['hours']:
        if not start <= h['ts'] < start + hours * 3600:
            continue
        label = local_time_text(snapshot, h['ts'], '%Hh')
        for key, field in (('temperature', 'feels'), ('precipitation', 'precip'), ('aqi', 'aqi'), ('wind', 'gust')):
            if h.get(field) is not None:
                out[key].append({'label': label, 'value': round(h[field], 1)})
    return out


def rule_based_advice(assessment):
    """Fixed, non-AI recommendations — always available, even when the AI is down."""
    if assessment['outdoor'] == 'unknown':
        return ['Les données sont insuffisantes : consultez la source officielle de votre région avant toute activité.']
    by_key = {i['key']: i for i in assessment['indicators'] if i['level'] is not None}

    def at_least(key, level):
        return key in by_key and by_key[key]['level'] >= level

    advice = []
    if at_least('temperature', 2):
        advice.append('Évitez l’effort en extérieur aux heures les plus chaudes ou froides ; privilégiez une mission en intérieur.')
    if at_least('precipitation', 2):
        advice.append('Fortes pluies attendues : reportez les activités de plein air ou prévoyez un repli en salle.')
    if at_least('wind', 2):
        advice.append('Rafales importantes : évitez stands, installations légères ou plantations en extérieur.')
    if at_least('uv', 2):
        advice.append('UV élevés : évitez le milieu de journée et protégez-vous (couvre-chef, crème, eau).')
    if at_least('aqi', 2) or at_least('pm25', 2):
        advice.append('Air dégradé : limitez les efforts intenses à l’extérieur, surtout pour les personnes sensibles.')
    if not advice and assessment['outdoor'] == 'caution':
        advice.append('Quelques précautions suffisent : surveillez l’évolution des conditions avant de partir.')
    if not advice:
        advice.append('Conditions favorables : une mission en extérieur (mobilité douce, nettoyage, plantation) est envisageable.')
    return advice


INDOOR_MISSIONS = [
    {'title': 'Chasse aux veilles électriques', 'category': 'energy', 'difficulty': 'easy', 'setting': 'indoor',
     'description': 'Quand il fait mauvais dehors, réduisez la consommation cachée de votre logement ou bureau.',
     'instructions': ['Repérez les appareils laissés en veille', 'Branchez-les sur des multiprises à interrupteur',
                      'Éteignez-les chaque soir pendant la durée du défi'], 'duration_days': 5, 'required_actions': 3},
    {'title': 'Tri et anti-gaspillage à la maison', 'category': 'recycling', 'difficulty': 'easy', 'setting': 'indoor',
     'description': 'Profitez d’une journée à l’intérieur pour organiser le tri et réduire les déchets.',
     'instructions': ['Installez un bac de tri par matière', 'Triez vos déchets pendant plusieurs jours',
                      'Cuisinez un repas avec des restes'], 'duration_days': 7, 'required_actions': 3},
]
OUTDOOR_MISSIONS = [
    {'title': 'Semaine de mobilité douce', 'category': 'transport', 'difficulty': 'easy', 'setting': 'outdoor',
     'description': 'Les conditions sont favorables : remplacez vos trajets motorisés courts par la marche ou le vélo.',
     'instructions': ['Choisissez 3 trajets courts habituels', 'Faites-les à pied ou à vélo',
                      'Notez les kilomètres évités'], 'duration_days': 7, 'required_actions': 3},
]


def suggested_missions(assessment):
    """Fixed mission templates matched to the conditions (outdoor only when the rules allow it)."""
    if assessment['outdoor'] == 'unknown':
        return []
    if assessment['outdoor'] == 'suitable':
        return [dict(OUTDOOR_MISSIONS[0]), dict(INDOOR_MISSIONS[1])]
    if assessment['outdoor'] == 'caution':
        return [dict(INDOOR_MISSIONS[1]), dict(OUTDOOR_MISSIONS[0], duration_days=5)]
    return [dict(m) for m in INDOOR_MISSIONS]
