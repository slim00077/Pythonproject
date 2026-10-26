"""Language-model layer shared by EcoPulse and EcoProof AI (Google Gemini, official ``google-genai`` SDK).

The model only *explains* measurements that ``rules.py`` already validated and
classified, and drafts challenge proposals. It receives the figures as input,
is told never to invent or recompute them, and its answer is strictly
validated before anything is displayed or saved. Credentials (``GEMINI_API_KEY``, ``GEMINI_MODEL``) come from the
server environment only and are never logged or shown to users; diagnostics go to the server log.
"""
import json
import logging
import re
import time
from dataclasses import dataclass

from django.conf import settings
from google import genai
from google.genai import errors as genai_errors
from google.genai import types as genai_types

from challenges.models import Challenge
from core.choices import EcoCategory

logger = logging.getLogger('ecoteams.ecopulse')

# google-genai raises transport errors from whichever HTTP client it uses (httpx2 in recent releases, httpx before).
_HTTP_MODULES = []
for _name in ('httpx2', 'httpx'):
    try:
        _HTTP_MODULES.append(__import__(_name))
    except ImportError:
        pass
TIMEOUT_ERRORS = tuple(m.TimeoutException for m in _HTTP_MODULES) + (TimeoutError,)
TRANSPORT_ERRORS = tuple(m.TransportError for m in _HTTP_MODULES) + (OSError,)

MAX_PROPOSALS = 2
MAX_RECOMMENDATIONS = 5

SYSTEM_PROMPT = """Tu es l'assistant « EcoPulse » de la plateforme française EcoTeams (défis écologiques entre équipes).
On te fournit, au format JSON, des conditions environnementales DÉJÀ mesurées et classées par des règles
déterministes. Ton rôle : les expliquer simplement, recommander des actions écologiques adaptées et sûres, et
proposer au maximum deux défis EcoTeams adaptés aux conditions.

Règles impératives :
- N'utilise QUE les valeurs et niveaux fournis. N'invente aucune mesure, ne recalcule aucun seuil, ne change aucun niveau.
- Si une donnée est « indisponible », dis-le ; ne la devine pas.
- Tu n'es PAS une alerte officielle : ne parle jamais d'« alerte », de « vigilance » ni de consigne des autorités.
- Si les conditions extérieures sont « unsuitable » (déconseillées), ne propose AUCUNE activité en extérieur :
  recommande une mission d'intérieur (énergie, recyclage, alimentation, eau, consommation responsable).
- Si des événements prévus sont signalés comme exposés (event_exposure), recommande à l'organisateur de revoir ou
  reporter l'événement, sans affirmer qu'il doit être annulé.
- Propose uniquement des actions sûres, sans effort intense ni risque pour la santé. Aucun conseil médical.
- Les défis sont de simples propositions soumises à validation humaine : ne mentionne ni points ni récompense.
- Réponds en français, ton clair et concis.

Réponds UNIQUEMENT par un objet JSON (sans texte autour, sans bloc de code) de la forme :
{
  "summary": "2 à 3 phrases expliquant la situation",
  "recommendations": [{"title": "...", "detail": "...", "setting": "indoor" | "outdoor"}],
  "event_advice": "conseil pour les événements exposés, ou chaîne vide",
  "proposals": [{
    "title": "... (max 100 caractères)",
    "category": "transport|recycling|energy|water|consumption|food",
    "difficulty": "easy|medium|hard",
    "setting": "indoor" | "outdoor",
    "description": "... (max 600 caractères)",
    "instructions": ["étape 1", "étape 2", "étape 3"],
    "duration_days": 1 à 14,
    "required_actions": 1 à 10
  }],
  "limitations": "limites de l'analyse en une phrase"
}"""


UNAVAILABLE_NOTICE = 'Le service d’analyse intelligente est temporairement indisponible. Vous pouvez continuer manuellement.'


class AIError(Exception):
    """The AI step failed; the message is safe to display (French, no technical detail)."""


class AIRequestRejected(AIError):
    """The provider refused the request itself (HTTP 400), e.g. an unusable image."""


@dataclass
class ModelReply:
    """What the rest of the application needs from a Gemini answer (keeps the SDK out of the callers)."""
    text: str
    finish_reason: str = 'STOP'
    output_tokens: int = 0


_warned_unconfigured = False


def is_configured():
    """True when both the key and the model id are set. Logs the diagnostic (once) on the server when they are not."""
    global _warned_unconfigured
    configured = bool(settings.GEMINI_API_KEY and settings.GEMINI_MODEL)
    if not configured and not _warned_unconfigured:
        _warned_unconfigured = True
        missing = [name for name, value in (('GEMINI_API_KEY', settings.GEMINI_API_KEY),
                                           ('GEMINI_MODEL', settings.GEMINI_MODEL)) if not value]
        logger.warning('Gemini AI disabled: environment variable(s) %s not set (see README, section IA).',
                       ', '.join(missing))
    return configured


def _client():
    return genai.Client(
        api_key=settings.GEMINI_API_KEY,
        http_options=genai_types.HttpOptions(timeout=int(settings.ECOPULSE_AI_TIMEOUT * 1000)),
    )


def _parts(content):
    """``content`` is a string, or a list mixing strings and ``{'image': bytes, 'mime_type': str}`` items."""
    if isinstance(content, str):
        return [content]
    return [
        genai_types.Part.from_bytes(data=item['image'], mime_type=item['mime_type']) if isinstance(item, dict) else item
        for item in content
    ]


def _generate(client, system, content, max_tokens, thinking, model=None):
    config = genai_types.GenerateContentConfig(
        system_instruction=system, max_output_tokens=max_tokens, response_mime_type='application/json', temperature=0.4,
        thinking_config=genai_types.ThinkingConfig(thinking_level=thinking) if thinking else None,
    )
    return client.models.generate_content(model=model or settings.GEMINI_MODEL, contents=_parts(content), config=config)


def create_message(system, content, max_tokens=4000):
    """Single call point to Gemini (patched in tests). Returns a ``ModelReply``; raises SDK errors untouched."""
    client = _client()  # keep a reference: the SDK closes its HTTP client when the Client object is collected
    models = [settings.GEMINI_MODEL]
    if settings.GEMINI_FALLBACK_MODEL and settings.GEMINI_FALLBACK_MODEL != settings.GEMINI_MODEL:
        models.append(settings.GEMINI_FALLBACK_MODEL)
    for index, model in enumerate(models):
        try:
            try:
                response = _generate(client, system, content, max_tokens, settings.GEMINI_THINKING_LEVEL, model)
            except genai_errors.ClientError as exc:
                if not (settings.GEMINI_THINKING_LEVEL and exc.code == 400 and 'thinking' in str(exc.message).lower()):
                    raise
                logger.info('Gemini model %s does not accept thinking_level: retrying without it', model)
                response = _generate(client, system, content, max_tokens, '', model)
            break
        except genai_errors.APIError as exc:
            if index == len(models) - 1 or exc.code not in (429, 504, 404):
                raise
            logger.warning('Gemini model %s failed (HTTP %s): switching to fallback model %s', model, exc.code, models[index + 1])
    candidate = response.candidates[0] if response.candidates else None
    reason = getattr(getattr(candidate, 'finish_reason', None), 'name', None) or 'STOP'
    feedback = getattr(response, 'prompt_feedback', None)
    if feedback is not None and getattr(feedback, 'block_reason', None):
        reason = 'PROMPT_BLOCKED'
    try:
        text = response.text or ''
    except (ValueError, AttributeError):
        text = ''
    usage = getattr(response, 'usage_metadata', None)
    return ModelReply(text=text, finish_reason=reason, output_tokens=getattr(usage, 'candidates_token_count', 0) or 0)


def _create_message(context_json):
    """Single call point of the EcoPulse analysis (patched in tests)."""
    return create_message(SYSTEM_PROMPT, f'Conditions validées (JSON) :\n{context_json}')


def build_context(snapshot, assessment, location_name, events, account_kind):
    """The only data sent to the model: validated figures, never raw provider payloads or personal data."""
    from . import rules
    indicators = [
        {
            'name': i['label'], 'unit': i['unit'], 'value': None if i['value'] is None else round(i['value'], 1),
            'minimum_value': None if i.get('minimum') is None else round(i['minimum'], 1),
            'level': i['level_label'], 'level_number': i['level'],
        }
        for i in assessment['indicators']
    ]
    return {
        'location': location_name,
        'forecast_period': {
            'from': rules.local_time_text(snapshot, assessment['start_ts']),
            'to': rules.local_time_text(snapshot, assessment['end_ts']), 'hours': assessment['hours'],
        },
        'indicators': indicators,
        'overall_level': assessment['overall_label'],
        'outdoor_suitability': assessment['outdoor'],
        'user_space': account_kind,
        'scheduled_events': [
            {'title': e['title'], 'starts': e['start_text'], 'exposure_level': e['level_label'],
             'outdoor_suitability': e['outdoor']}
            for e in events
        ],
        'disclaimer': 'Données Open-Meteo ; classification indicative, pas une alerte officielle.',
    }


def _extract_json(text):
    text = text.strip()
    fenced = re.match(r'^```(?:json)?\s*(.*?)\s*```$', text, re.DOTALL)
    if fenced:
        text = fenced.group(1)
    try:
        return json.loads(text)
    except ValueError:
        start, end = text.find('{'), text.rfind('}')
        if start != -1 and end > start:
            try:
                return json.loads(text[start:end + 1])
            except ValueError:
                pass
    raise AIError('La réponse de l’analyse n’a pas pu être interprétée. Réessayez.')


def _text(value, limit, required=False):
    if not isinstance(value, str):
        if required:
            raise AIError('La réponse de l’IA est incomplète. Réessayez.')
        return ''
    value = ' '.join(value.split())[:limit]
    if required and not value:
        raise AIError('La réponse de l’IA est incomplète. Réessayez.')
    return value


FORBIDDEN_WORDS = re.compile(r'\b(alerte officielle|vigilance (orange|rouge|jaune)|alerte (rouge|orange))\b', re.I)


def validate_payload(payload, outdoor):
    """Strict validation + safety guards. Returns a clean dict or raises AIError."""
    if not isinstance(payload, dict):
        raise AIError('La réponse de l’IA est invalide. Réessayez.')
    summary = _text(payload.get('summary'), 900, required=True)
    recommendations = []
    for item in (payload.get('recommendations') or [])[:MAX_RECOMMENDATIONS * 2]:
        if not isinstance(item, dict):
            continue
        title, detail = _text(item.get('title'), 120), _text(item.get('detail'), 400)
        setting = item.get('setting') if item.get('setting') in ('indoor', 'outdoor') else 'indoor'
        if not title:
            continue
        if outdoor == 'unsuitable' and setting == 'outdoor':
            continue  # the rules said outdoor is unsuitable: never display such a suggestion
        recommendations.append({'title': title, 'detail': detail, 'setting': setting})
    recommendations = recommendations[:MAX_RECOMMENDATIONS]
    proposals = []
    categories = set(EcoCategory.values)
    difficulties = set(Challenge.Difficulty.values)
    for item in (payload.get('proposals') or [])[:MAX_PROPOSALS * 3]:
        if not isinstance(item, dict):
            continue
        setting = item.get('setting') if item.get('setting') in ('indoor', 'outdoor') else 'indoor'
        if outdoor == 'unsuitable' and setting == 'outdoor':
            continue
        steps = [_text(s, 200) for s in (item.get('instructions') or []) if isinstance(s, str)]
        steps = [s for s in steps if s][:8]
        try:
            title = _text(item.get('title'), 100, required=True)
            description = _text(item.get('description'), 600, required=True)
        except AIError:
            continue
        if item.get('category') not in categories or not steps:
            continue
        difficulty = item.get('difficulty') if item.get('difficulty') in difficulties else Challenge.Difficulty.EASY
        proposals.append({
            'title': title, 'category': item['category'], 'difficulty': difficulty, 'setting': setting,
            'description': description, 'instructions': steps,
            'duration_days': _bounded_int(item.get('duration_days'), 1, 14, 7),
            'required_actions': _bounded_int(item.get('required_actions'), 1, 10, 3),
        })
    proposals = proposals[:MAX_PROPOSALS]
    texts = [summary] + [r['title'] + ' ' + r['detail'] for r in recommendations]
    if any(FORBIDDEN_WORDS.search(t) for t in texts):
        raise AIError('La réponse de l’IA a été rejetée (formulation assimilable à une alerte officielle). Réessayez.')
    return {
        'summary': summary, 'recommendations': recommendations,
        'event_advice': _text(payload.get('event_advice'), 500),
        'proposals': proposals, 'limitations': _text(payload.get('limitations'), 300),
    }


def _bounded_int(value, low, high, default):
    if isinstance(value, bool) or not isinstance(value, int):
        return default
    return max(low, min(high, value))


BLOCKED_REASONS = {'SAFETY', 'PROHIBITED_CONTENT', 'BLOCKLIST', 'SPII', 'IMAGE_SAFETY', 'PROMPT_BLOCKED', 'RECITATION'}


def _api_error(exc, label):
    """Translate a Gemini SDK error into an ``AIError`` with a safe French message; details go to the server log."""
    code = getattr(exc, 'code', None)
    detail = f'{getattr(exc, "status", "")} {getattr(exc, "message", "")}'.lower()
    if code in (401, 403) or 'api key' in detail or 'api_key' in detail:
        logger.error('%s AI: credentials rejected by Gemini (HTTP %s) - check GEMINI_API_KEY', label, code)
        return AIError(UNAVAILABLE_NOTICE)
    if code == 429:
        logger.warning('%s AI: Gemini quota or rate limit reached (HTTP 429)', label)
        return AIError('Le service d’analyse est très sollicité. Réessayez dans quelques minutes ou continuez manuellement.')
    if code == 404:
        logger.error('%s AI: model %r not found for this account - check GEMINI_MODEL', label, settings.GEMINI_MODEL)
        return AIError(UNAVAILABLE_NOTICE)
    if code == 400:
        logger.warning('%s AI: request rejected (HTTP 400): %s', label, getattr(exc, 'status', ''))
        return AIRequestRejected('Le service d’analyse a refusé la requête.')
    logger.error('%s AI: Gemini error (HTTP %s)', label, code)
    return AIError('Le service d’analyse a rencontré une erreur. Réessayez plus tard ou continuez manuellement.')


def call_model(call, label='EcoPulse'):
    """Run ``call()`` and return ``(response_text, reply, elapsed_seconds)``.

    Provider failures become ``AIError`` with a French message that is safe to display (no stack trace, no
    credential or configuration detail). Shared by every AI feature so errors are handled the same way.
    """
    if not is_configured():
        raise AIError(UNAVAILABLE_NOTICE)
    started = time.monotonic()
    try:
        try:
            reply = call()
        except genai_errors.ServerError as exc:
            if getattr(exc, 'code', None) != 503:
                raise
            logger.info('%s AI: Gemini temporarily overloaded (503), retrying once', label)
            time.sleep(3)
            reply = call()
    except genai_errors.APIError as exc:
        raise _api_error(exc, label) from exc
    except TIMEOUT_ERRORS as exc:
        logger.warning('%s AI: timeout after %.1f s', label, time.monotonic() - started)
        raise AIError(f'L’analyse n’a pas répondu en {settings.ECOPULSE_AI_TIMEOUT} s. Réessayez plus tard.') from exc
    except TRANSPORT_ERRORS as exc:
        logger.warning('%s AI: network error (%s)', label, type(exc).__name__)
        raise AIError('Le service d’analyse est injoignable pour le moment. Vous pouvez continuer manuellement.') from exc
    elapsed = time.monotonic() - started
    if reply.finish_reason in BLOCKED_REASONS:
        raise AIError('L’analyse n’a pas pu traiter cette demande.')
    if reply.finish_reason == 'MAX_TOKENS':
        raise AIError('La réponse de l’analyse a été tronquée. Réessayez.')
    if not (reply.text or '').strip():
        raise AIError('Le service d’analyse n’a renvoyé aucune réponse exploitable.')
    return reply.text, reply, elapsed


def analyze(context, outdoor):
    """Call the model and return ``(validated_result, elapsed_seconds)``."""
    text, response, elapsed = call_model(
        lambda: _create_message(json.dumps(context, ensure_ascii=False, sort_keys=True)))
    result = validate_payload(_extract_json(text), outdoor)
    logger.info('EcoPulse AI answered in %.2f s (model=%s, output_tokens=%s)', elapsed, settings.GEMINI_MODEL,
                response.output_tokens)
    return result, elapsed
