"""Local keyword-based category and tag suggestions for community events."""
import re
import unicodedata

from core.choices import EcoCategory


CATEGORY_RULES = {
    EcoCategory.TRANSPORT: {
        'keywords': ('velo', 'vélo', 'mobilite', 'mobilité', 'transport', 'marche', 'covoiturage', 'bus'),
        'tags': ('#MobiliteDouce', '#TransportDurable'),
    },
    EcoCategory.RECYCLING: {
        'keywords': ('recyclage', 'recycler', 'tri', 'dechet', 'déchet', 'plastique', 'nettoyage', 'collecte'),
        'tags': ('#Recyclage', '#ZeroDechet'),
    },
    EcoCategory.ENERGY: {
        'keywords': ('energie', 'énergie', 'electricite', 'électricité', 'solaire', 'sobriete', 'sobriété'),
        'tags': ('#Energie', '#SobrieteEnergetique'),
    },
    EcoCategory.WATER: {
        'keywords': ('eau', 'riviere', 'rivière', 'ocean', 'océan', 'mer', 'plage', 'bassin'),
        'tags': ('#ProtectionDeLEau', '#PreservationDesMilieux'),
    },
    EcoCategory.CONSUMPTION: {
        'keywords': ('consommation', 'reparation', 'réparation', 'reemploi', 'réemploi', 'local', 'durable'),
        'tags': ('#ConsommationResponsable', '#Reemploi'),
    },
    EcoCategory.FOOD: {
        'keywords': ('alimentaire', 'alimentation', 'repas', 'nourriture', 'gaspillage', 'compost', 'cuisine'),
        'tags': ('#AntiGaspi', '#AlimentationDurable'),
    },
}


def _normalize(text):
    decomposed = unicodedata.normalize('NFKD', text.casefold())
    return ''.join(char for char in decomposed if not unicodedata.combining(char))


def suggest_event_tags(title, description):
    """Suggest one category and relevant hashtags from event title and description."""
    normalized = _normalize(f'{title} {description}')
    scores = {}
    matched_tags = []
    for category, rules in CATEGORY_RULES.items():
        keywords = {_normalize(keyword) for keyword in rules['keywords']}
        matches = {
            keyword for keyword in keywords
            if re.search(rf'(?<!\w){re.escape(keyword)}(?!\w)', normalized)
        }
        scores[category] = len(matches)
        if matches:
            matched_tags.extend(rules['tags'])

    best_category = max(scores, key=scores.get)
    suggested_category = best_category if scores[best_category] else None
    tags = list(dict.fromkeys(matched_tags))
    return {
        'category': suggested_category,
        'category_label': dict(EcoCategory.choices).get(suggested_category) if suggested_category else None,
        'tags': tags[:6],
    }
