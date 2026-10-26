"""EcoPulse tests: every external call (Open-Meteo, Claude API) is mocked — no network is used."""
import json
import socket
import time
from datetime import datetime, timedelta, timezone as dt_timezone
from unittest import mock
from urllib.error import HTTPError, URLError

import httpx2
from django.core.cache import cache
from google.genai import errors as genai_errors
from django.test import Client, SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from challenges.models import Challenge
from core.exceptions import BusinessRuleError
from core.testing import make_event, make_user
from gamification.models import PointTransaction

from . import ai, providers, rules, services

NOW = int(time.time())
FIELDS = {
    'forecast': {'temperature_2m': 22, 'apparent_temperature': 22, 'precipitation_probability': 10,
                 'precipitation': 0, 'wind_gusts_10m': 15},
    'air': {'european_aqi': 15, 'pm2_5': 6, 'uv_index': 2},
}


def make_payloads(hours=72, forecast=None, air=None, drop=()):
    """Open-Meteo-shaped payloads starting at the current hour (UTC, offset 0). Values may be lists."""
    start = rules.hour_floor(NOW)
    times = [datetime.fromtimestamp(start + i * 3600, dt_timezone.utc).strftime('%Y-%m-%dT%H:%M') for i in range(hours)]

    def block(defaults, overrides):
        values = {**defaults, **(overrides or {})}
        out = {'time': times}
        for key, value in values.items():
            if key in drop:
                continue
            out[key] = value if isinstance(value, list) else [value] * hours
        return out

    fc = {'utc_offset_seconds': 0, 'timezone': 'GMT', 'hourly': block(FIELDS['forecast'], forecast),
          'current': {'temperature_2m': 22, 'apparent_temperature': 22}}
    aq = {'utc_offset_seconds': 0, 'timezone': 'GMT', 'hourly': block(FIELDS['air'], air),
          'current': {'european_aqi': 15, 'pm2_5': 6, 'uv_index': 2}}
    return fc, aq


LOCATION = {'name': 'Tunis, Tunisie', 'lat': 36.8065, 'lon': 10.1815}


def snapshot_from(forecast=None, air=None, **kw):
    fc, aq = make_payloads(forecast=forecast, air=air, **kw)
    return rules.build_snapshot(LOCATION, fc, aq, timezone.now())


def assess(forecast=None, air=None, hours=24, **kw):
    snap = snapshot_from(forecast, air, **kw)
    return rules.evaluate_period(snap, NOW, hours)


def level_of(assessment, key):
    return next(i for i in assessment['indicators'] if i['key'] == key)['level']


class RulesTests(SimpleTestCase):
    def test_clear_day_is_suitable(self):
        result = assess()
        self.assertEqual(result['outdoor'], 'suitable')
        self.assertEqual(result['overall_level'], 0)
        self.assertEqual(result['hours'], 24)

    def test_heatwave_is_unsuitable(self):
        result = assess(forecast={'apparent_temperature': 38, 'temperature_2m': 36}, air={'uv_index': 9})
        self.assertEqual(result['outdoor'], 'unsuitable')
        self.assertEqual(level_of(result, 'temperature'), 2)
        self.assertEqual(level_of(result, 'uv'), 3)
        self.assertEqual({t['key'] for t in result['triggers']}, {'temperature', 'uv'})

    def test_storm_is_critical(self):
        result = assess(forecast={'precipitation': 12, 'wind_gusts_10m': 85})
        self.assertEqual(result['overall_level'], 3)
        self.assertEqual(result['overall_label'], 'Critique')

    def test_polluted_air_is_unsuitable(self):
        result = assess(air={'european_aqi': 90, 'pm2_5': 55})
        self.assertEqual(level_of(result, 'aqi'), 3)
        self.assertEqual(level_of(result, 'pm25'), 3)
        self.assertEqual(result['outdoor'], 'unsuitable')

    def test_cold_uses_the_minimum(self):
        result = assess(forecast={'apparent_temperature': [10] * 5 + [-1] * 19 + [10] * 48})
        self.assertEqual(level_of(result, 'temperature'), 2)

    def test_threshold_boundaries_are_inclusive(self):
        cases = [
            ('wind', {'wind_gusts_10m': 39.9}, 0), ('wind', {'wind_gusts_10m': 40}, 1),
            ('wind', {'wind_gusts_10m': 59.9}, 1), ('wind', {'wind_gusts_10m': 60}, 2),
            ('wind', {'wind_gusts_10m': 80}, 3),
            ('temperature', {'apparent_temperature': 29.9}, 0), ('temperature', {'apparent_temperature': 30}, 1),
            ('temperature', {'apparent_temperature': 35}, 2), ('temperature', {'apparent_temperature': 40}, 3),
            ('temperature', {'apparent_temperature': 5}, 1), ('temperature', {'apparent_temperature': 5.1}, 0),
            ('temperature', {'apparent_temperature': 0}, 2), ('temperature', {'apparent_temperature': -5}, 3),
            ('precipitation', {'precipitation': 1.9}, 0), ('precipitation', {'precipitation': 2}, 1),
        ]
        for key, forecast, expected in cases:
            with self.subTest(key=key, forecast=forecast):
                self.assertEqual(level_of(assess(forecast=forecast), key), expected)
        for key, air, expected in [('aqi', {'european_aqi': 39}, 0), ('aqi', {'european_aqi': 40}, 1),
                                   ('uv', {'uv_index': 2.9}, 0), ('uv', {'uv_index': 3}, 1),
                                   ('pm25', {'pm2_5': 15}, 1), ('pm25', {'pm2_5': 14.9}, 0)]:
            with self.subTest(key=key, air=air):
                self.assertEqual(level_of(assess(air=air), key), expected)

    @override_settings(ECOPULSE_THRESHOLDS={'wind': [10, 20, 30]})
    def test_thresholds_are_configurable(self):
        self.assertEqual(level_of(assess(forecast={'wind_gusts_10m': 25}), 'wind'), 2)

    def test_missing_series_makes_indicator_unavailable_not_zero(self):
        result = assess(drop=('wind_gusts_10m',))
        wind = next(i for i in result['indicators'] if i['key'] == 'wind')
        self.assertFalse(wind['available'])
        self.assertIsNone(wind['value'])
        self.assertIsNone(wind['level'])
        self.assertEqual(result['outdoor'], 'suitable')  # other indicators still evaluated

    def test_null_values_inside_series_are_skipped_and_flagged_partial(self):
        result = assess(forecast={'wind_gusts_10m': [None] * 12 + [50] * 60})
        wind = next(i for i in result['indicators'] if i['key'] == 'wind')
        self.assertEqual(wind['level'], 1)
        self.assertTrue(wind['partial'])

    def test_implausible_and_non_numeric_values_are_rejected(self):
        snap = snapshot_from(air={'european_aqi': [900] * 72, 'pm2_5': ['n/a'] * 72, 'uv_index': [float('nan')] * 72})
        result = rules.evaluate_period(snap, NOW, 24)
        for key in ('aqi', 'pm25', 'uv'):
            self.assertFalse(next(i for i in result['indicators'] if i['key'] == key)['available'])
        self.assertTrue(snap['warnings'])

    def test_everything_missing_is_unknown(self):
        fc, aq = make_payloads(drop=tuple(list(FIELDS['forecast']) + list(FIELDS['air'])))
        snap = rules.build_snapshot(LOCATION, fc, aq, timezone.now())
        result = rules.evaluate_period(snap, NOW, 24)
        self.assertEqual(result['outdoor'], 'unknown')
        self.assertIsNone(result['overall_level'])

    def test_one_service_missing(self):
        fc, _ = make_payloads()
        snap = rules.build_snapshot(LOCATION, fc, None, timezone.now())
        self.assertEqual(snap['missing_services'], ['qualité de l’air'])
        result = rules.evaluate_period(snap, NOW, 24)
        self.assertFalse(next(i for i in result['indicators'] if i['key'] == 'aqi')['available'])

    def test_no_hourly_data_raises(self):
        with self.assertRaises(ValueError):
            rules.build_snapshot(LOCATION, {'hourly': {}}, {'hourly': {'time': []}}, timezone.now())

    def test_event_exposure_and_coverage(self):
        snap = snapshot_from(forecast={'precipitation': [0] * 10 + [12] * 62})
        start = rules.hour_floor(NOW) + 12 * 3600
        wet = rules.event_exposure(snap, start, start + 7200)
        self.assertTrue(wet['covered'])
        self.assertEqual(wet['outdoor'], 'unsuitable')
        dry = rules.event_exposure(snap, rules.hour_floor(NOW), rules.hour_floor(NOW) + 3600)
        self.assertEqual(dry['outdoor'], 'suitable')
        far = rules.event_exposure(snap, NOW + 10 * 86400, NOW + 10 * 86400 + 3600)
        self.assertFalse(far['covered'])

    def test_rule_based_advice_follows_conditions(self):
        self.assertIn('intérieur', ' '.join(rules.rule_based_advice(assess(forecast={'apparent_temperature': 38}))))
        self.assertIn('favorables', ' '.join(rules.rule_based_advice(assess())))
        unknown = rules.evaluate_period(
            rules.build_snapshot(LOCATION, *make_payloads(drop=tuple(list(FIELDS['forecast']) + list(FIELDS['air']))),
                                 timezone.now()), NOW, 24)
        self.assertIn('insuffisantes', rules.rule_based_advice(unknown)[0])


class ProviderTests(SimpleTestCase):
    def _call(self, side_effect=None, body=b'{}'):
        response = mock.MagicMock()
        response.__enter__.return_value.read.return_value = body
        with mock.patch('ecopulse.providers.urlopen', side_effect=side_effect, return_value=response):
            return providers.fetch_forecast(36.8, 10.1, 3)

    def test_success(self):
        self.assertEqual(self._call(body=b'{"hourly": {}}'), {'hourly': {}})

    def test_timeout(self):
        with self.assertRaisesMessage(providers.ProviderError, 'n’a pas répondu'):
            self._call(side_effect=socket.timeout())

    def test_timeout_wrapped_in_urlerror(self):
        with self.assertRaisesMessage(providers.ProviderError, 'n’a pas répondu'):
            self._call(side_effect=URLError(socket.timeout()))

    def test_network_down(self):
        with self.assertRaisesMessage(providers.ProviderError, 'injoignable'):
            self._call(side_effect=URLError('no route'))

    def test_http_429_and_500(self):
        with self.assertRaisesMessage(providers.ProviderError, 'limite'):
            self._call(side_effect=HTTPError('u', 429, 'x', {}, None))
        with self.assertRaisesMessage(providers.ProviderError, '500'):
            self._call(side_effect=HTTPError('u', 500, 'x', {}, None))

    def test_invalid_json_and_wrong_shape(self):
        with self.assertRaisesMessage(providers.ProviderError, 'illisible'):
            self._call(body=b'<html>')
        with self.assertRaisesMessage(providers.ProviderError, 'inattendue'):
            self._call(body=b'[1, 2]')

    def test_api_level_error_flag(self):
        with self.assertRaises(providers.ProviderError):
            self._call(body=b'{"error": true, "reason": "bad"}')


@override_settings(GEMINI_API_KEY='test-key', GEMINI_MODEL='test-model', ECOPULSE_AI_MAX_PER_HOUR=3)
class ServiceTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = make_user('alice')

    def patch_providers(self, **kw):
        fc, aq = make_payloads(**kw)
        return (mock.patch('ecopulse.providers.fetch_forecast', return_value=fc),
                mock.patch('ecopulse.providers.fetch_air_quality', return_value=aq))

    def test_snapshot_is_cached(self):
        p1, p2 = self.patch_providers()
        with p1 as forecast, p2 as air:
            _, first = services.get_snapshot(LOCATION)
            _, second = services.get_snapshot(LOCATION)
        self.assertEqual((first['origin'], second['origin']), ('live', 'cache'))
        self.assertEqual((forecast.call_count, air.call_count), (1, 1))

    def test_stale_copy_is_used_when_services_fail(self):
        p1, p2 = self.patch_providers()
        with p1, p2:
            services.get_snapshot(LOCATION)
        err = providers.ProviderError('Le service météo est injoignable.')
        with mock.patch('ecopulse.providers.fetch_forecast', side_effect=err), \
                mock.patch('ecopulse.providers.fetch_air_quality', side_effect=err):
            snap, meta = services.get_snapshot(LOCATION, force=True)
        self.assertEqual(meta['origin'], 'stale')
        self.assertIn('injoignable', meta['error'])
        self.assertTrue(snap['hours'])

    def test_unavailable_without_any_cache(self):
        err = providers.ProviderError('Le service météo est injoignable.')
        with mock.patch('ecopulse.providers.fetch_forecast', side_effect=err), \
                mock.patch('ecopulse.providers.fetch_air_quality', side_effect=err):
            with self.assertRaises(services.EnvironmentUnavailable):
                services.get_snapshot(LOCATION)

    def test_partial_failure_still_returns_data(self):
        fc, _ = make_payloads()
        with mock.patch('ecopulse.providers.fetch_forecast', return_value=fc), \
                mock.patch('ecopulse.providers.fetch_air_quality', side_effect=providers.ProviderError('KO')):
            snap, meta = services.get_snapshot(LOCATION)
        self.assertEqual(snap['missing_services'], ['qualité de l’air'])
        self.assertEqual(meta['origin'], 'live')

    def test_garbage_payload_is_unavailable(self):
        with mock.patch('ecopulse.providers.fetch_forecast', return_value={'hourly': {'time': ['x']}}), \
                mock.patch('ecopulse.providers.fetch_air_quality', return_value={}):
            with self.assertRaises(services.EnvironmentUnavailable):
                services.get_snapshot(LOCATION)

    @override_settings(ECOPULSE_MAX_PROVIDER_CALLS_PER_HOUR=2)
    def test_hourly_provider_quota(self):
        p1, p2 = self.patch_providers()
        with p1, p2:
            services.get_snapshot(LOCATION)  # spends 2 calls
            with self.assertRaises(services.EnvironmentUnavailable):
                services.get_snapshot({**LOCATION, 'lat': 10.0}, force=True)

    def test_refresh_cooldown(self):
        p1, p2 = self.patch_providers()
        with p1, p2:
            services.request_refresh(self.user, LOCATION)
            with self.assertRaises(BusinessRuleError):
                services.request_refresh(self.user, LOCATION)

    def test_resolve_location(self):
        place = {'name': 'Sfax', 'admin1': 'Sfax', 'country': 'Tunisie', 'latitude': 34.74, 'longitude': 10.76}
        with mock.patch('ecopulse.providers.geocode', return_value=[place]) as geocode:
            first = services.resolve_location('Sfax')
            services.resolve_location('Sfax')
        self.assertEqual(geocode.call_count, 1)
        self.assertEqual(first['name'], 'Sfax, Tunisie')
        with mock.patch('ecopulse.providers.geocode', return_value=[]):
            with self.assertRaises(BusinessRuleError):
                services.resolve_location('Zzzzqq')
        with self.assertRaises(BusinessRuleError):
            services.resolve_location('', 95, 10)
        self.assertEqual(services.resolve_location('Labo', 10, 20)['lat'], 10.0)

    def test_events_exposure_only_for_own_onsite_events(self):
        other = make_user('bob')
        mine = make_event(self.user, 'Plantation', start_in_hours=5, location='Parc')
        make_event(other, 'Autre événement', start_in_hours=5)
        make_event(self.user, 'En ligne', start_in_hours=5, format='online')
        snap = snapshot_from(forecast={'precipitation': 12})
        rows = services.events_exposure(self.user, snap)
        self.assertEqual([r['event'] for r in rows], [mine])
        self.assertTrue(rows[0]['needs_review'])


def ai_message(payload, stop_reason='STOP', text=None):
    """A Gemini answer as the application sees it (``ai.ModelReply``): no network, no SDK object."""
    return ai.ModelReply(text=text if text is not None else json.dumps(payload), finish_reason=stop_reason,
                         output_tokens=10)


GOOD_PAYLOAD = {
    'summary': 'Conditions favorables aujourd’hui.',
    'recommendations': [
        {'title': 'Sortie vélo', 'detail': 'Profitez-en.', 'setting': 'outdoor'},
        {'title': 'Tri des déchets', 'detail': 'À la maison.', 'setting': 'indoor'},
    ],
    'event_advice': '',
    'proposals': [
        {'title': 'Semaine à vélo', 'category': 'transport', 'difficulty': 'easy', 'setting': 'outdoor',
         'description': 'Se déplacer à vélo.', 'instructions': ['Planifier', 'Rouler'], 'duration_days': 7,
         'required_actions': 3},
        {'title': 'Chasse au gaspillage électrique', 'category': 'energy', 'difficulty': 'easy', 'setting': 'indoor',
         'description': 'Débrancher les veilles.', 'instructions': ['Repérer', 'Débrancher'], 'duration_days': 5,
         'required_actions': 2},
    ],
    'limitations': 'Analyse indicative.',
}


def api_error(code, status='ERROR', message='detail'):
    error_class = genai_errors.ClientError if code < 500 else genai_errors.ServerError
    return error_class(code, {'error': {'message': message, 'status': status}}, None)


@override_settings(GEMINI_API_KEY='test-key', GEMINI_MODEL='test-model')
class AITests(SimpleTestCase):
    def analyze(self, message=None, side_effect=None, outdoor='suitable'):
        with mock.patch('ecopulse.ai._create_message', return_value=message, side_effect=side_effect), \
                mock.patch('ecopulse.ai.time.sleep'):
            return ai.analyze({'x': 1}, outdoor)

    def test_overloaded_503_is_retried_once_then_succeeds(self):
        result, _ = self.analyze(side_effect=[api_error(503, 'UNAVAILABLE'), ai_message(GOOD_PAYLOAD)])
        self.assertEqual(len(result['proposals']), 2)

    @override_settings(GEMINI_FALLBACK_MODEL='backup-model')
    def test_quota_error_switches_to_the_fallback_model(self):
        reply = mock.Mock(candidates=[mock.Mock()], prompt_feedback=None, usage_metadata=None, text='{}')
        reply.candidates[0].finish_reason.name = 'STOP'
        with mock.patch('ecopulse.ai.genai.Client') as client:
            client.return_value.models.generate_content.side_effect = [api_error(429, 'RESOURCE_EXHAUSTED'), reply]
            self.assertEqual(ai.create_message('s', 'c').text, '{}')
        models = [c.kwargs['model'] for c in client.return_value.models.generate_content.call_args_list]
        self.assertEqual(models, ['test-model', 'backup-model'])

    @override_settings(GEMINI_FALLBACK_MODEL='')
    def test_quota_error_without_fallback_is_reported(self):
        with mock.patch('ecopulse.ai.genai.Client') as client:
            client.return_value.models.generate_content.side_effect = api_error(429, 'RESOURCE_EXHAUSTED')
            with self.assertRaises(genai_errors.ClientError):
                ai.create_message('s', 'c')

    def test_asset_tag_versions_static_files_so_browsers_drop_stale_css(self):
        from django.template import Context, Template
        html = Template("{% load eco_tags %}{% asset 'css/ecoteams.css' %}").render(Context())
        self.assertRegex(html, r'/static/css/ecoteams\.css\?v=\d+')

    def test_other_server_errors_are_not_retried(self):
        with mock.patch('ecopulse.ai._create_message', side_effect=api_error(500, 'INTERNAL')) as create, \
                mock.patch('ecopulse.ai.time.sleep'), self.assertRaises(ai.AIError):
            ai.analyze({'x': 1}, 'suitable')
        self.assertEqual(create.call_count, 1)

    @override_settings(GEMINI_THINKING_LEVEL='LOW')
    def test_model_without_thinking_level_is_retried_without_it(self):
        reply = mock.Mock(candidates=[mock.Mock()], prompt_feedback=None, usage_metadata=None, text='{}')
        reply.candidates[0].finish_reason.name = 'STOP'
        refusing = api_error(400, 'INVALID_ARGUMENT', 'Thinking level is not supported for this model')
        with mock.patch('ecopulse.ai.genai.Client') as client:
            client.return_value.models.generate_content.side_effect = [refusing, reply]
            ai.create_message('s', 'c')
        configs = [c.kwargs['config'] for c in client.return_value.models.generate_content.call_args_list]
        self.assertIsNotNone(configs[0].thinking_config)
        self.assertIsNone(configs[1].thinking_config)

    def test_success(self):
        result, elapsed = self.analyze(ai_message(GOOD_PAYLOAD))
        self.assertEqual(len(result['proposals']), 2)
        self.assertGreaterEqual(elapsed, 0)

    def test_json_in_code_fence_is_accepted(self):
        text = '```json\n' + json.dumps(GOOD_PAYLOAD) + '\n```'
        result, _ = self.analyze(ai_message(None, text=text))
        self.assertEqual(result['summary'], GOOD_PAYLOAD['summary'])

    def test_unsuitable_conditions_drop_outdoor_content(self):
        result, _ = self.analyze(ai_message(GOOD_PAYLOAD), outdoor='unsuitable')
        self.assertEqual([p['setting'] for p in result['proposals']], ['indoor'])
        self.assertEqual([r['setting'] for r in result['recommendations']], ['indoor'])

    def test_invalid_proposals_are_dropped_and_values_bounded(self):
        payload = {**GOOD_PAYLOAD, 'proposals': [
            {**GOOD_PAYLOAD['proposals'][0], 'category': 'magic'},
            {**GOOD_PAYLOAD['proposals'][1], 'instructions': []},
            {**GOOD_PAYLOAD['proposals'][1], 'duration_days': 900, 'required_actions': -4, 'difficulty': 'insane'},
            'not a dict',
        ]}
        result, _ = self.analyze(ai_message(payload))
        self.assertEqual(len(result['proposals']), 1)
        proposal = result['proposals'][0]
        self.assertEqual((proposal['duration_days'], proposal['required_actions'], proposal['difficulty']), (14, 1, 'easy'))

    def test_official_alert_wording_is_rejected(self):
        payload = {**GOOD_PAYLOAD, 'summary': 'Alerte officielle : restez chez vous.'}
        with self.assertRaisesMessage(ai.AIError, 'alerte officielle'):
            self.analyze(ai_message(payload))

    def test_missing_summary_and_garbage(self):
        with self.assertRaises(ai.AIError):
            self.analyze(ai_message({**GOOD_PAYLOAD, 'summary': ''}))
        with self.assertRaisesMessage(ai.AIError, 'interprétée'):
            self.analyze(ai_message(None, text='Désolé, je ne peux pas.'))
        with self.assertRaises(ai.AIError):
            self.analyze(ai_message(None, text='[1, 2]'))

    def test_refusal_truncation_and_empty(self):
        with self.assertRaisesMessage(ai.AIError, 'pas pu traiter'):
            self.analyze(ai_message(GOOD_PAYLOAD, stop_reason='SAFETY'))
        with self.assertRaisesMessage(ai.AIError, 'tronquée'):
            self.analyze(ai_message(GOOD_PAYLOAD, stop_reason='MAX_TOKENS'))
        with self.assertRaisesMessage(ai.AIError, 'aucune réponse'):
            self.analyze(ai_message(None, text='  '))

    def test_api_errors_become_ai_errors_without_technical_detail(self):
        cases = [
            (httpx2.ReadTimeout('slow'), 'pas répondu'),
            (httpx2.ConnectError('down'), 'injoignable'),
            (api_error(401, 'UNAUTHENTICATED', 'secret key problem'), ai.UNAVAILABLE_NOTICE),
            (api_error(400, 'INVALID_ARGUMENT', 'API key not valid. Please pass a valid API key.'), ai.UNAVAILABLE_NOTICE),
            (api_error(403, 'PERMISSION_DENIED'), ai.UNAVAILABLE_NOTICE),
            (api_error(404, 'NOT_FOUND', 'model not found'), ai.UNAVAILABLE_NOTICE),
            (api_error(429, 'RESOURCE_EXHAUSTED', 'quota'), 'sollicité'),
            (api_error(503, 'UNAVAILABLE'), 'rencontré une erreur'),
        ]
        for exc, fragment in cases:
            with self.subTest(exc=repr(exc)[:60]):
                with self.assertLogs('ecoteams.ecopulse', level='WARNING'):
                    with self.assertRaises(ai.AIError) as caught:
                        self.analyze(side_effect=exc)
                self.assertIn(fragment, str(caught.exception))
                for leak in ('GEMINI', 'ANTHROPIC', 'API key', 'secret', 'quota', 'model'):
                    self.assertNotIn(leak, str(caught.exception))

    def test_bad_request_is_a_rejected_request(self):
        with self.assertRaises(ai.AIRequestRejected):
            self.analyze(side_effect=api_error(400, 'INVALID_ARGUMENT', 'bad image'))

    @override_settings(GEMINI_API_KEY='')
    def test_not_configured(self):
        with self.assertRaisesMessage(ai.AIError, 'temporairement indisponible'):
            ai.analyze({}, 'suitable')

    @override_settings(GEMINI_API_KEY='test-key', GEMINI_MODEL='')
    def test_a_model_id_is_required(self):
        self.assertFalse(ai.is_configured())

    @override_settings(GEMINI_API_KEY='test-key', GEMINI_MODEL='the-model')
    def test_sdk_call_uses_configured_model_and_never_leaks_the_key(self):
        reply = mock.Mock(candidates=[mock.Mock(finish_reason=mock.Mock())], prompt_feedback=None,
                          usage_metadata=mock.Mock(candidates_token_count=7))
        reply.candidates[0].finish_reason.name = 'STOP'
        reply.text = '{"summary": "x"}'
        with mock.patch('ecopulse.ai.genai.Client') as client:
            client.return_value.models.generate_content.return_value = reply
            out = ai.create_message('system', ['texte', {'image': b'\xff\xd8', 'mime_type': 'image/jpeg'}])
        kwargs = client.return_value.models.generate_content.call_args.kwargs
        self.assertEqual(kwargs['model'], 'the-model')
        self.assertEqual(len(kwargs['contents']), 2)
        self.assertEqual((out.text, out.finish_reason, out.output_tokens), ('{"summary": "x"}', 'STOP', 7))
        self.assertEqual(client.call_args.kwargs['api_key'], 'test-key')

    def test_context_contains_only_validated_figures(self):
        snap = snapshot_from(forecast={'wind_gusts_10m': 50})
        assessment = rules.evaluate_period(snap, NOW, 24)
        context = ai.build_context(snap, assessment, 'Tunis', [], 'student')
        wind = next(i for i in context['indicators'] if i['name'] == 'Rafales de vent')
        self.assertEqual((wind['value'], wind['level']), (50.0, 'Modéré'))
        self.assertNotIn('lat', json.dumps(context))


@override_settings(GEMINI_API_KEY='test-key', GEMINI_MODEL='test-model', ECOPULSE_AI_MAX_PER_HOUR=3)
class ViewTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = make_user('alice')

    def patch_providers(self, **kw):
        fc, aq = make_payloads(**kw)
        stack = mock.patch.multiple('ecopulse.providers', fetch_forecast=mock.Mock(return_value=fc),
                                    fetch_air_quality=mock.Mock(return_value=aq))
        return stack

    def test_login_required(self):
        for name in ('dashboard',):
            response = self.client.get(reverse(f'ecopulse:{name}'))
            self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.post(reverse('ecopulse:analysis')).status_code, 302)

    def test_dashboard_shows_real_values_units_and_attribution(self):
        self.client.force_login(self.user)
        with self.patch_providers(forecast={'wind_gusts_10m': 47, 'apparent_temperature': 31}):
            response = self.client.get(reverse('ecopulse:dashboard'))
        self.assertContains(response, 'Open-Meteo.com')
        self.assertContains(response, 'Tunis, Tunisie')
        self.assertContains(response, '47')
        self.assertContains(response, 'km/h')
        self.assertContains(response, 'Données récupérées à')
        self.assertContains(response, 'pas une alerte officielle')
        self.assertEqual(response.context['assessment']['outdoor'], 'caution')

    def test_dashboard_error_state_when_provider_down(self):
        self.client.force_login(self.user)
        err = providers.ProviderError('Le service météo est injoignable.')
        with mock.patch.multiple('ecopulse.providers', fetch_forecast=mock.Mock(side_effect=err),
                                 fetch_air_quality=mock.Mock(side_effect=err)):
            response = self.client.get(reverse('ecopulse:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Données environnementales indisponibles')
        self.assertNotContains(response, 'km/h')

    def test_invalid_period_falls_back_to_24h(self):
        self.client.force_login(self.user)
        with self.patch_providers():
            response = self.client.get(reverse('ecopulse:dashboard') + '?hours=9999')
        self.assertEqual(response.context['hours'], 24)

    def test_set_location_stored_in_session(self):
        self.client.force_login(self.user)
        self.client.post(reverse('ecopulse:location'), {'query': 'Labo', 'latitude': '10.5', 'longitude': '20.5'})
        self.assertEqual(self.client.session['ecopulse_location']['lat'], 10.5)
        self.client.post(reverse('ecopulse:location'), {'query': '', 'latitude': '10.5', 'longitude': ''})
        self.assertEqual(self.client.session['ecopulse_location']['name'], 'Labo')  # unchanged by invalid form

    def generate(self, payload=GOOD_PAYLOAD, **provider_kw):
        with self.patch_providers(**provider_kw), mock.patch('ecopulse.ai._create_message',
                                                              return_value=ai_message(payload)) as create:
            response = self.client.post(reverse('ecopulse:analysis'))
        return response, create

    def test_ai_analysis_endpoint_and_cache(self):
        self.client.force_login(self.user)
        response, create = self.generate()
        data = response.json()
        self.assertTrue(data['ok'])
        self.assertEqual(len(data['proposals']), 2)
        self.assertFalse(data['from_cache'])
        response2, create2 = self.generate()
        self.assertTrue(response2.json()['from_cache'])
        self.assertEqual(create2.call_count, 0)

    def test_analysis_json_has_every_field_the_page_script_renders(self):
        self.client.force_login(self.user)
        data = self.generate()[0].json()
        for key in ('ok', 'summary', 'recommendations', 'event_advice', 'proposals', 'limitations', 'batch_id',
                    'basis', 'model', 'elapsed', 'from_cache'):
            self.assertIn(key, data)
        self.assertIn('Tunis', data['basis'])
        self.assertIn('Open-Meteo', data['basis'])

    def test_failed_analysis_is_json_not_html_and_leaks_nothing(self):
        self.client.force_login(self.user)
        with self.patch_providers(), mock.patch('ecopulse.ai._create_message', side_effect=api_error(
                401, 'UNAUTHENTICATED', 'API key not valid: secret-key-123')):
            response = self.client.post(reverse('ecopulse:analysis'))
        self.assertEqual(response['Content-Type'], 'application/json')
        self.assertEqual(response.status_code, 502)
        self.assertEqual(response.json()['error'], ai.UNAVAILABLE_NOTICE)
        self.assertNotIn('secret-key-123', response.content.decode())

    def test_ai_error_is_reported_as_json(self):
        self.client.force_login(self.user)
        with self.patch_providers(), mock.patch('ecopulse.ai._create_message', side_effect=httpx2.ReadTimeout('slow')):
            response = self.client.post(reverse('ecopulse:analysis'))
        self.assertEqual(response.status_code, 502)
        self.assertFalse(response.json()['ok'])

    def test_ai_user_rate_limit(self):
        self.client.force_login(self.user)
        statuses = []
        for i in range(5):
            # Distinct conditions each time so the AI cache cannot absorb the calls.
            cache.delete('ecopulse:snap:36.81:10.18')
            response, _ = self.generate(forecast={'wind_gusts_10m': 10 + i * 0.5})
            statuses.append(response.status_code)
        self.assertEqual(statuses, [200, 200, 200, 502, 502])
        self.assertIn('Limite', response.json()['error'])

    @override_settings(GEMINI_API_KEY='')
    def test_ai_disabled_without_key(self):
        self.client.force_login(self.user)
        with self.patch_providers():
            page = self.client.get(reverse('ecopulse:dashboard'))
            self.assertContains(page, 'temporairement indisponible')
            self.assertNotContains(page, 'ANTHROPIC')
            self.assertNotContains(page, 'GEMINI')
            self.assertNotContains(page, '.env')
            self.assertContains(page, '<button class="btn btn-primary" type="button" id="ep-ai-run"')
            response = self.client.post(reverse('ecopulse:analysis'))
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()['error'], ai.UNAVAILABLE_NOTICE)

    def test_ai_refused_when_data_missing(self):
        self.client.force_login(self.user)
        every = tuple(list(FIELDS['forecast']) + list(FIELDS['air']))
        response, create = self.generate(drop=every)
        self.assertEqual(response.status_code, 422)
        self.assertEqual(create.call_count, 0)

    def test_unsuitable_conditions_never_get_outdoor_proposals(self):
        self.client.force_login(self.user)
        response, _ = self.generate(forecast={'apparent_temperature': 41})
        self.assertEqual([p['setting'] for p in response.json()['proposals']], ['indoor'])

    def save(self, batch, index=0, mode='draft'):
        return self.client.post(reverse('ecopulse:save_proposal'), {'batch': batch, 'index': index, 'mode': mode})

    def test_proposal_saved_as_private_draft_without_points(self):
        self.client.force_login(self.user)
        data = self.generate()[0].json()
        response = self.save(data['batch_id'], 0, 'draft')
        challenge = Challenge.objects.get()
        self.assertRedirects(response, challenge.get_absolute_url())
        self.assertEqual(challenge.status, Challenge.Status.DRAFT)
        self.assertEqual(challenge.creator, self.user)
        self.assertEqual(challenge.reward_points, 0)
        self.assertIsNone(challenge.published_at)
        self.assertIn('EcoPulse IA', challenge.description)
        self.assertFalse(PointTransaction.objects.exists())
        self.assertRedirects(self.save(data['batch_id'], 0), reverse('ecopulse:dashboard'), fetch_redirect_response=False)
        self.assertEqual(Challenge.objects.count(), 1)  # no duplicate

    def test_proposal_submitted_for_approval(self):
        self.client.force_login(self.user)
        data = self.generate()[0].json()
        response = self.save(data['batch_id'], 1, 'pending')
        challenge = Challenge.objects.get()
        self.assertRedirects(response, challenge.get_absolute_url())
        self.assertEqual(challenge.status, Challenge.Status.PENDING)
        self.assertIsNone(challenge.published_at)
        # Not visible in the public catalogue until a reviewer approves it.
        self.assertNotContains(self.client.get(reverse('challenges:list')), challenge.title)

    def test_save_rejects_tampering(self):
        self.client.force_login(self.user)
        data = self.generate()[0].json()
        dashboard = reverse('ecopulse:dashboard')
        for args in (('wrong-batch', 0), (data['batch_id'], 9), (data['batch_id'], 'x'), (data['batch_id'], 0, 'active')):
            self.assertRedirects(self.save(*args), dashboard, fetch_redirect_response=False)
        self.assertFalse(Challenge.objects.exists())

    def test_cannot_save_another_users_batch(self):
        self.client.force_login(self.user)
        data = self.generate()[0].json()
        self.client.force_login(make_user('mallory'))
        self.assertRedirects(self.save(data['batch_id'], 0), reverse('ecopulse:dashboard'), fetch_redirect_response=False)
        self.assertFalse(Challenge.objects.exists())

    def test_event_at_risk_is_displayed(self):
        make_event(self.user, 'Plantation du parc', start_in_hours=6, location='Parc Belvédère')
        self.client.force_login(self.user)
        with self.patch_providers(forecast={'precipitation': 15}):
            response = self.client.get(reverse('ecopulse:dashboard'))
        self.assertContains(response, 'Plantation du parc')
        self.assertContains(response, 'reporter')


@override_settings(GEMINI_API_KEY='')
class FrontendContractTests(SimpleTestCase):
    """Regression tests for the endless loader / red bar: static contracts of the templates, CSS and scripts."""
    root = __import__('pathlib').Path(__file__).resolve().parents[1]

    def read(self, relative):
        return (self.root / relative).read_text(encoding='utf-8')

    def test_hidden_attribute_always_wins_over_component_display_rules(self):
        # .ep-loading { display: grid } and .alert { display: flex } used to override [hidden]: the skeleton and an
        # empty red alert bar were permanently visible.
        self.assertIn('[hidden] { display: none !important; }', self.read('static/css/ecoteams.css'))

    def test_loader_and_error_boxes_start_hidden(self):
        pages = (('templates/ecopulse/dashboard.html', ('ep-ai-loading', 'ep-ai-error', 'ep-ai-result')),
                 ('templates/challenges/_ecoproof.html', ('ecoproof-loading', 'ecoproof-error', 'ecoproof-results')))
        for template, ids in pages:
            html = self.read(template)
            for element_id in ids:
                self.assertRegex(html, rf'id="{element_id}"[^>]*\bhidden\b|\bhidden\b[^>]*id="{element_id}"', element_id)

    def test_scripts_declare_every_element_variable_they_use_and_ids_exist_in_templates(self):
        # A missing `var runButton` made the script throw at load: the button silently did nothing.
        import re
        pairs = (('static/js/ecopulse.js', 'templates/ecopulse/dashboard.html'),
                 ('static/js/ecoproof.js', 'templates/challenges/_ecoproof.html'))
        for script, template in pairs:
            source, html = self.read(script), self.read(template)
            for variable, element_id in re.findall(r"var (\w+) = document\.getElementById\('([\w-]+)'\)", source):
                self.assertIn(f'id="{element_id}"', html, f'{script}: #{element_id} missing from {template}')
            declared = set(re.findall(r'var (\w+)\b', source)) | set(re.findall(r'function (\w+)', source))
            for name in ('runButton', 'analyzeButton', 'loading', 'errorBox', 'errorText', 'result', 'results', 'panel',
                         'running', 'TIMEOUT_MS'):
                if re.search(rf'\b{name}\b', source):
                    self.assertIn(name, declared, f'{script}: {name} is used but never declared')

    def test_scripts_reset_the_loader_in_finally_and_guard_double_clicks(self):
        for script in ('static/js/ecopulse.js', 'static/js/ecoproof.js'):
            source = self.read(script)
            self.assertIn('finally {', source, script)
            self.assertRegex(source, r'loading\.hidden = true;\s*\n?\s*(runButton|analyzeButton)\.disabled = false', script)
            self.assertIn('if (running) { return; }', source, script)
            self.assertIn('AbortController', source, script)
            self.assertNotIn('.then(function () { loading.hidden', source, script)


class RuleMissionTests(TestCase):
    """Missions that need neither the AI nor a key, and the card on the challenge catalogue."""

    def setUp(self):
        cache.clear()
        self.user = make_user('alice')
        self.client.force_login(self.user)

    def patch_providers(self, **kw):
        fc, aq = make_payloads(**kw)
        return mock.patch.multiple('ecopulse.providers', fetch_forecast=mock.Mock(return_value=fc),
                                   fetch_air_quality=mock.Mock(return_value=aq))

    def test_suggested_missions_follow_conditions(self):
        self.assertEqual([m['setting'] for m in rules.suggested_missions(assess())], ['outdoor', 'indoor'])
        hot = rules.suggested_missions(assess(forecast={'apparent_temperature': 41}))
        self.assertEqual({m['setting'] for m in hot}, {'indoor'})
        unknown = rules.evaluate_period(snapshot_from(drop=tuple(list(FIELDS['forecast']) + list(FIELDS['air']))), NOW, 24)
        self.assertEqual(rules.suggested_missions(unknown), [])

    def test_dashboard_shows_recommendations_and_ai_panel_before_the_visual(self):
        with self.patch_providers():
            html = self.client.get(reverse('ecopulse:dashboard')).content.decode()
        self.assertLess(html.index('Analyse IA et missions adaptatives'), html.index('ep-globe'))
        self.assertLess(html.index('Recommandations'), html.index('ep-globe'))
        self.assertIn('Missions adaptées aux conditions', html)

    def test_rule_mission_saved_as_draft_without_any_ai(self):
        with self.patch_providers():
            batch = self.client.get(reverse('ecopulse:dashboard')).context['rule_batch']
        response = self.client.post(reverse('ecopulse:save_proposal'), {'batch': batch['id'], 'index': 0, 'mode': 'draft'})
        challenge = Challenge.objects.get()
        self.assertRedirects(response, challenge.get_absolute_url())
        self.assertEqual(challenge.status, Challenge.Status.DRAFT)
        self.assertEqual(challenge.reward_points, 0)
        self.assertIn('EcoPulse (règles)', challenge.description)
        with self.patch_providers():  # reload: the saved mission is shown as saved, not savable twice
            page = self.client.get(reverse('ecopulse:dashboard'))
        self.assertContains(page, challenge.get_absolute_url())

    def test_dashboard_renders_real_buttons_and_post_forms(self):
        with self.patch_providers():
            html = self.client.get(reverse('ecopulse:dashboard')).content.decode()
        self.assertIn('<button class="btn btn-primary" type="button" id="ep-ai-run"', html)  # even without a key
        action = reverse('ecopulse:save_proposal')
        self.assertGreaterEqual(html.count(f'<form method="post" action="{action}"'), 4)
        self.assertRegex(html, r'<button type="submit" class="btn btn-primary btn-sm">[^<]*(<[^>]+>[^<]*)*Soumettre à validation')
        self.assertIn('name="csrfmiddlewaretoken"', html)

    def test_submitting_a_mission_redirects_and_awards_nothing(self):
        with self.patch_providers():
            batch = self.client.get(reverse('ecopulse:dashboard')).context['rule_batch']
        response = self.client.post(reverse('ecopulse:save_proposal'), {'batch': batch['id'], 'index': 0, 'mode': 'pending'})
        challenge = Challenge.objects.get()
        self.assertRedirects(response, challenge.get_absolute_url(), fetch_redirect_response=False)
        self.assertEqual(challenge.status, Challenge.Status.PENDING)  # pending review, never active
        self.assertEqual((challenge.creator, challenge.reward_points), (self.user, 0))
        self.assertIsNone(challenge.published_at)
        self.assertFalse(PointTransaction.objects.exists())
        page = self.client.get(response.url)
        self.assertContains(page, 'Défi soumis à validation')

    def test_save_requires_post_login_and_csrf(self):
        url = reverse('ecopulse:save_proposal')
        self.assertEqual(self.client.get(url).status_code, 405)
        self.assertEqual(Client().post(url, {}).status_code, 302)
        strict = Client(enforce_csrf_checks=True)
        strict.force_login(self.user)
        self.assertEqual(strict.post(url, {'batch': 'x', 'index': 0, 'mode': 'pending'}).status_code, 403)

    def test_heat_gives_only_indoor_rule_missions(self):
        with self.patch_providers(forecast={'apparent_temperature': 41}):
            batch = self.client.get(reverse('ecopulse:dashboard')).context['rule_batch']
        self.assertEqual({i['setting'] for i in batch['items']}, {'indoor'})

    def test_plain_links_between_challenges_and_ecopulse(self):
        challenges = self.client.get(reverse('challenges:list'))
        self.assertContains(challenges, reverse('ecopulse:dashboard'))
        with self.patch_providers():
            ecopulse = self.client.get(reverse('ecopulse:dashboard'))
        self.assertContains(ecopulse, reverse('challenges:list'))
        self.assertContains(ecopulse, 'Défis et conditions en direct')
