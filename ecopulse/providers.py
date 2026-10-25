"""Open-Meteo clients (forecast, air quality, geocoding).

Only the standard library is used. Every function raises ``ProviderError``
with a French message that is safe to show to the user; nothing here
interprets the data (see ``rules.py``). Data by Open-Meteo.com (CC BY 4.0),
free tier for non-commercial use.
"""
import json
import logging
import socket
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from django.conf import settings

logger = logging.getLogger('ecoteams.ecopulse')

FORECAST_URL = 'https://api.open-meteo.com/v1/forecast'
AIR_QUALITY_URL = 'https://air-quality-api.open-meteo.com/v1/air-quality'
GEOCODING_URL = 'https://geocoding-api.open-meteo.com/v1/search'
MAX_BODY_BYTES = 2_000_000

FORECAST_HOURLY = 'temperature_2m,apparent_temperature,precipitation_probability,precipitation,wind_gusts_10m'
AIR_HOURLY = 'european_aqi,pm2_5,uv_index'


class ProviderError(Exception):
    """The external service failed or answered with unusable data."""


def _get_json(url, params):
    timeout = settings.ECOPULSE_HTTP_TIMEOUT
    request = Request(f'{url}?{urlencode(params)}', headers={
        'User-Agent': 'EcoTeams-EcoPulse/1.0 (university project)', 'Accept': 'application/json',
    })
    started = time.monotonic()
    try:
        with urlopen(request, timeout=timeout) as response:  # noqa: S310 - fixed https endpoints
            body = response.read(MAX_BODY_BYTES + 1)
    except HTTPError as exc:
        logger.warning('Open-Meteo HTTP %s on %s', exc.code, url)
        if exc.code == 429:
            raise ProviderError('Le service météo limite temporairement les requêtes. Réessayez plus tard.') from exc
        raise ProviderError(f'Le service météo a répondu par une erreur ({exc.code}).') from exc
    except (socket.timeout, TimeoutError) as exc:
        raise ProviderError(f'Le service météo n’a pas répondu en {timeout} s.') from exc
    except URLError as exc:
        if isinstance(exc.reason, (socket.timeout, TimeoutError)):
            raise ProviderError(f'Le service météo n’a pas répondu en {timeout} s.') from exc
        raise ProviderError('Le service météo est injoignable (réseau indisponible).') from exc
    except OSError as exc:
        raise ProviderError('Le service météo est injoignable.') from exc
    logger.info('Open-Meteo %s answered in %.0f ms', url.split('/')[2], (time.monotonic() - started) * 1000)
    if len(body) > MAX_BODY_BYTES:
        raise ProviderError('Réponse du service météo anormalement volumineuse.')
    try:
        data = json.loads(body)
    except ValueError as exc:
        raise ProviderError('Réponse du service météo illisible.') from exc
    if not isinstance(data, dict):
        raise ProviderError('Réponse du service météo inattendue.')
    if data.get('error'):
        raise ProviderError('Le service météo a refusé la requête.')
    return data


def fetch_forecast(lat, lon, days):
    return _get_json(FORECAST_URL, {
        'latitude': f'{lat:.4f}', 'longitude': f'{lon:.4f}', 'hourly': FORECAST_HOURLY,
        'current': 'temperature_2m,apparent_temperature', 'forecast_days': days, 'timezone': 'auto',
    })


def fetch_air_quality(lat, lon, days):
    return _get_json(AIR_QUALITY_URL, {
        'latitude': f'{lat:.4f}', 'longitude': f'{lon:.4f}', 'hourly': AIR_HOURLY,
        'current': 'european_aqi,pm2_5,uv_index', 'forecast_days': days, 'timezone': 'auto',
    })


def geocode(query):
    """Return up to 5 places ``{name, country, admin1, latitude, longitude}``."""
    data = _get_json(GEOCODING_URL, {'name': query, 'count': 5, 'language': 'fr', 'format': 'json'})
    results = data.get('results') or []
    return [r for r in results if isinstance(r, dict) and 'latitude' in r and 'longitude' in r]
