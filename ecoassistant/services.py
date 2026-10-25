"""Gemini-backed eco advice, with catalogue data kept authoritative in Django."""

import json
import logging
import re
import ssl

from django.conf import settings

from actions.models import EcoActionType

logger = logging.getLogger('ecoteams')


class AssistantError(Exception):
    """A user-safe error raised when the assistant cannot answer."""


def _catalogue():
    return list(EcoActionType.objects.filter(is_active=True).order_by('category', 'name'))


def _matching_actions(question, actions):
    words = set(re.findall(r'[\wÀ-ÿ]+', question.lower()))
    scored = []
    for action in actions:
        haystack = ' '.join((action.name, action.description, action.category, action.unit)).lower()
        score = sum(1 for word in words if len(word) > 3 and word in haystack)
        scored.append((score, action))
    scored.sort(key=lambda item: (-item[0], item[1].name))
    selected = [action for score, action in scored if score]
    return (selected or actions)[:3]


def _catalogue_context(actions):
    return '\n'.join(
        f'- slug={action.slug}; name={action.name}; category={action.get_category_display()}; '
        f'points={action.points}; unit={action.unit or "none"}; description={action.description}'
        for action in actions
    ) or '- No active ecological action is currently available.'


def _parse_json_response(text):
    cleaned = (text or '').strip()
    if cleaned.startswith('```'):
        cleaned = re.sub(r'^```(?:json)?\s*', '', cleaned, flags=re.IGNORECASE)
        cleaned = re.sub(r'\s*```$', '', cleaned).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r'\{.*\}', cleaned, flags=re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


def ask(user, question, history=None):
    question = (question or '').strip()
    if not question:
        raise AssistantError('Écrivez une question ou un objectif écologique.')
    if len(question) > 2000:
        raise AssistantError('Votre message est trop long (maximum 2000 caractères).')

    actions = _catalogue()
    fallback_actions = _matching_actions(question, actions)
    fallback_answer = (
        'Commencez par une habitude simple et régulière, puis mesurez votre progression. '
        'Les recommandations ci-dessous proviennent du catalogue actif EcoTeams.'
    )
    api_key = getattr(settings, 'GEMINI_API_KEY', '')
    if not api_key:
        return fallback_answer + '\n\nLe service IA est momentanément désactivé.', fallback_actions

    try:
        import httpx
        import truststore
        from google import genai
        from google.genai import types

        recent_history = '\n'.join(
            f"{item.get('role', 'user')}: {item.get('content', '')}"
            for item in (history or [])[-6:]
        ) or 'Aucune conversation précédente.'

        prompt = f"""Tu es Eco-Assistant dans l'application EcoTeams.
Réponds en français, de manière pratique, courte et personnalisée.
Tu peux conseiller des habitudes générales pour économiser l'eau, l'énergie et réduire le CO2.
RÈGLE ABSOLUE : ne crée jamais d'action, de nom, de slug, de point ou de facteur CO2.
Pour les recommandations, utilise uniquement les slugs présents dans le catalogue ci-dessous.
Retourne uniquement un JSON valide avec exactement deux clés :
{{"answer": "conseil pratique", "recommended_slugs": ["slug-existant"]}}
Maximum 3 slugs. Si aucun ne correspond, retourne une liste vide.

Catalogue actif réel :
{_catalogue_context(actions)}

Question de l'utilisateur : {question}

Conversation récente :
{recent_history}
"""
        # Use the Windows certificate store. This avoids the common Python 3.13
        # certificate error on student machines without disabling TLS verification.
        ssl_context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        http_client = httpx.Client(verify=ssl_context, timeout=30.0)
        client = genai.Client(
            api_key=api_key,
            http_options=types.HttpOptions(httpx_client=http_client),
        )
        try:
            response = None
            last_error = None
            models = list(dict.fromkeys([
                settings.GEMINI_MODEL,
                'gemini-flash-lite-latest',
                'gemini-flash-latest',
            ]))
            for model in models:
                try:
                    response = client.models.generate_content(
                        model=model,
                        contents=prompt,
                        config=types.GenerateContentConfig(
                            response_mime_type='application/json', temperature=0.4, max_output_tokens=500,
                        ),
                    )
                    break
                except Exception as exc:
                    last_error = exc
                    logger.warning('Gemini model %s failed; trying the next fallback.', model)
            if response is None:
                raise last_error
        finally:
            client.close()
            http_client.close()
        data = _parse_json_response(response.text)
        answer = str(data.get('answer', '')).strip() or fallback_answer
        requested_slugs = data.get('recommended_slugs', [])
        if not isinstance(requested_slugs, list):
            requested_slugs = []
        by_slug = {action.slug: action for action in actions}
        recommendations = [by_slug[slug] for slug in requested_slugs if slug in by_slug][:3]
        return answer, recommendations
    except Exception:
        logger.exception('Eco-Assistant Gemini request failed')
        return fallback_answer + '\n\nJe n’ai pas pu joindre le service IA. Voici une suggestion locale.', fallback_actions

