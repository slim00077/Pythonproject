"""AI-assisted evidence review for ecological action submissions.

This module never changes a submission status and never awards points. It only
returns an advisory report for a human moderator.
"""

import json
import logging
import ssl
import re
from io import BytesIO

import httpx
import truststore
from django.conf import settings
from PIL import Image, UnidentifiedImageError

from core.exceptions import BusinessRuleError

logger = logging.getLogger('ecoteams')

ALLOWED_IMAGE_MIME_TYPES = {
    'JPEG': 'image/jpeg',
    'PNG': 'image/png',
    'WEBP': 'image/webp',
}
RECOMMENDATIONS = {
    'supports_claim': 'Les éléments visibles sont compatibles avec la déclaration, à confirmer humainement.',
    'possible_mismatch': 'Les éléments visibles semblent ne pas correspondre complètement à la déclaration.',
    'insufficient_evidence': 'La photo ne fournit pas suffisamment d’éléments pour évaluer la déclaration.',
    'inconclusive': 'Le résultat est incertain : une vérification humaine approfondie est nécessaire.',
}


def _read_valid_image(submission):
    if not submission.evidence:
        raise BusinessRuleError('Aucune photo justificative n’est disponible pour l’analyse IA.')
    try:
        with submission.evidence.open('rb') as evidence_file:
            image_bytes = evidence_file.read()
        with Image.open(BytesIO(image_bytes)) as image:
            image.verify()
            image_format = image.format
    except (FileNotFoundError, OSError, UnidentifiedImageError) as exc:
        raise BusinessRuleError('La photo justificative est absente ou invalide.') from exc
    mime_type = ALLOWED_IMAGE_MIME_TYPES.get(image_format)
    if not mime_type:
        raise BusinessRuleError('Le format de la photo n’est pas compatible avec l’analyse IA.')
    return image_bytes, mime_type


def _normalise_report(payload):
    if not isinstance(payload, dict):
        raise ValueError('Gemini returned an invalid report.')
    elements = payload.get('detected_elements', [])
    if not isinstance(elements, list):
        elements = []
    elements = [str(item).strip() for item in elements if str(item).strip()][:10]
    try:
        confidence = max(0, min(100, int(payload.get('confidence_score', 0))))
    except (TypeError, ValueError):
        confidence = 0
    recommendation = payload.get('recommendation', 'inconclusive')
    if recommendation not in RECOMMENDATIONS:
        recommendation = 'inconclusive'
    return {
        'detected_elements': elements,
        'consistency_analysis': str(payload.get('consistency_analysis', '')).strip() or 'Analyse non disponible.',
        'confidence_score': confidence,
        'recommendation': recommendation,
        'recommendation_label': RECOMMENDATIONS[recommendation],
        'evidence_limitations': str(payload.get('evidence_limitations', '')).strip() or 'Aucune limite précisée.',
        'photo_readable': bool(payload.get('photo_readable', False)),
        'human_review_required': True,
    }


def _parse_json_response(text):
    """Accept JSON mode responses with occasional markdown wrappers safely."""
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


def validate_submission(submission):
    """Ask Gemini to review one pending submission without making a decision."""
    if submission.status != submission.Status.PENDING:
        raise BusinessRuleError('L’analyse IA est disponible uniquement pour une déclaration en attente.')
    image_bytes, mime_type = _read_valid_image(submission)
    api_key = getattr(settings, 'GEMINI_API_KEY', '').strip()
    if not api_key:
        raise BusinessRuleError('La clé Gemini n’est pas configurée dans le fichier .env.')

    action = submission.action_type
    prompt = f"""Tu es un assistant de pré-modération pour EcoTeams.
Analyse la photo et compare-la avec l'action écologique déclarée et la description de l'utilisateur.
IMPORTANT : une image seule ne prouve jamais que l'action a réellement eu lieu. Tu ne dois jamais approuver
ou refuser automatiquement. Ton résultat sert uniquement d'aide à un modérateur humain.
Ne donne aucun point et ne calcule aucun CO2.

Retourne uniquement un JSON valide avec ces clés :
{{
  "detected_elements": ["éléments clairement visibles"],
  "photo_readable": true,
  "consistency_analysis": "comparaison factuelle entre photo, action et description",
  "confidence_score": 0,
  "recommendation": "supports_claim|possible_mismatch|insufficient_evidence|inconclusive",
  "evidence_limitations": "ce que la photo ne permet pas de vérifier"
}}
Le score est un niveau de confiance dans l'analyse visuelle, de 0 à 100, pas une preuve de réalisation.
Reste prudent : si la photo est ambiguë ou générique, utilise inconclusive ou insufficient_evidence.

Action déclarée : {action.name}
Catégorie : {action.get_category_display()}
Description du catalogue : {action.description}
Consignes de validation : {action.instructions or 'Aucune consigne spécifique.'}
Description de l'utilisateur : {submission.description}
Quantité déclarée : {submission.quantity or 'Non renseignée'} {action.unit or ''}
Date déclarée : {submission.performed_on:%d/%m/%Y}
"""
    ssl_context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    http_client = httpx.Client(verify=ssl_context, timeout=30.0)
    from google import genai
    from google.genai import types

    client = genai.Client(
        api_key=api_key,
        http_options=types.HttpOptions(httpx_client=http_client),
    )
    try:
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
                    contents=[types.Part.from_bytes(data=image_bytes, mime_type=mime_type), prompt],
                    config=types.GenerateContentConfig(
                        response_mime_type='application/json', temperature=0.2, max_output_tokens=700,
                    ),
                )
                return _normalise_report(_parse_json_response(response.text))
            except (json.JSONDecodeError, ValueError) as exc:
                last_error = exc
                logger.warning('Gemini model %s returned an invalid report; trying the next model.', model)
            except Exception as exc:
                last_error = exc
                logger.warning('Gemini model %s failed; trying the next fallback.', model)
        logger.exception('Eco-Validator Gemini request failed', exc_info=last_error)
        if isinstance(last_error, (json.JSONDecodeError, ValueError)):
            raise BusinessRuleError('Le rapport IA est invalide. Le modérateur doit vérifier la photo manuellement.') from last_error
        raise BusinessRuleError('Le service IA est indisponible. La modération manuelle reste possible.') from last_error
    finally:
        client.close()
        http_client.close()

