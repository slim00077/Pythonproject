"""Language-model layer of EcoPulse (Anthropic Messages API, official SDK).

The model only *explains* measurements that ``rules.py`` already validated and
classified, and drafts challenge proposals. It receives the figures as input,
is told never to invent or recompute them, and its answer is strictly
validated before anything is displayed or saved. The API key comes from the
``ANTHROPIC_API_KEY`` environment variable only.
"""
import json
import logging
import re
import time

import anthropic
from django.conf import settings

from challenges.models import Challenge
from core.choices import EcoCategory

logger = logging.getLogger('ecoteams.ecopulse')

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


class AIError(Exception):
    """The AI step failed; the message is safe to display (French)."""


def is_configured():
    return bool(settings.ECOPULSE_AI_API_KEY)


def _client():
    return anthropic.Anthropic(
        api_key=settings.ECOPULSE_AI_API_KEY, timeout=settings.ECOPULSE_AI_TIMEOUT, max_retries=1,
    )


def _create_message(context_json):
    """Single call point (patched in tests)."""
    return _client().messages.create(
        model=settings.ECOPULSE_AI_MODEL,
        max_tokens=4000,
        output_config={'effort': 'low'},
        system=SYSTEM_PROMPT,
        messages=[{'role': 'user', 'content': f'Conditions validées (JSON) :\n{context_json}'}],
    )


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
    raise AIError('La réponse de l’IA n’a pas pu être interprétée. Réessayez.')


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
    for item in (payload.get('recommendations') or [])[:MAX_RECOMMENDATIONS]:
        if not isinstance(item, dict):
            continue
        title, detail = _text(item.get('title'), 120), _text(item.get('detail'), 400)
        setting = item.get('setting') if item.get('setting') in ('indoor', 'outdoor') else 'indoor'
        if not title:
            continue
        if outdoor == 'unsuitable' and setting == 'outdoor':
            continue  # the rules said outdoor is unsuitable: never display such a suggestion
        recommendations.append({'title': title, 'detail': detail, 'setting': setting})
    proposals = []
    categories = set(EcoCategory.values)
    difficulties = set(Challenge.Difficulty.values)
    for item in (payload.get('proposals') or [])[:MAX_PROPOSALS]:
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


def analyze(context, outdoor):
    """Call the model and return ``(validated_result, elapsed_seconds)``."""
    if not is_configured():
        raise AIError('L’analyse IA n’est pas configurée (variable ANTHROPIC_API_KEY absente).')
    started = time.monotonic()
    try:
        response = _create_message(json.dumps(context, ensure_ascii=False, sort_keys=True))
    except anthropic.APITimeoutError as exc:
        raise AIError(f'L’IA n’a pas répondu en {settings.ECOPULSE_AI_TIMEOUT} s. Réessayez plus tard.') from exc
    except anthropic.AuthenticationError as exc:
        logger.error('EcoPulse AI: authentication failed')
        raise AIError('La clé d’API de l’IA est refusée. Contactez un administrateur.') from exc
    except anthropic.RateLimitError as exc:
        raise AIError('Le service d’IA est saturé. Réessayez dans quelques minutes.') from exc
    except anthropic.APIConnectionError as exc:
        raise AIError('Le service d’IA est injoignable.') from exc
    except anthropic.APIStatusError as exc:
        logger.error('EcoPulse AI: API status %s', exc.status_code)
        raise AIError('Le service d’IA a renvoyé une erreur. Réessayez plus tard.') from exc
    elapsed = time.monotonic() - started
    if response.stop_reason == 'refusal':
        raise AIError('L’IA a refusé de traiter cette demande.')
    if response.stop_reason == 'max_tokens':
        raise AIError('La réponse de l’IA a été tronquée. Réessayez.')
    text = ''.join(block.text for block in response.content if getattr(block, 'type', '') == 'text')
    if not text.strip():
        raise AIError('L’IA n’a renvoyé aucune réponse exploitable.')
    result = validate_payload(_extract_json(text), outdoor)
    usage = getattr(response, 'usage', None)
    logger.info('EcoPulse AI answered in %.2f s (output_tokens=%s)', elapsed, getattr(usage, 'output_tokens', '?'))
    return result, elapsed
