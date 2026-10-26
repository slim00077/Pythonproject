"""Measure the AI goal coach on real goals: latency, tokens and automatic quality checks.

    python manage.py evaluate_goal_coach --limit 10 --output reports/coach_eval.json

Each advice is graded by objective criteria (the rubric below). The report is meant to be commented
during the oral: latency distribution, token usage, pass rate per criterion, failures.
"""
import json
import re
import statistics
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from core.exceptions import BusinessRuleError
from goals import ai
from goals.models import Goal

FRENCH_WORDS = {'vous', 'votre', 'vos', 'le', 'la', 'les', 'des', 'et', 'pour', 'de', 'un', 'une', 'est', 'sur'}
BAD_PROMISES = re.compile(r'(vous gagnerez|points? garantis?|badge garanti|je vous promets)', re.IGNORECASE)


def word_count(text):
    return len(re.findall(r'\w+', text))


def grade(goal, text):
    """Objective rubric: each criterion is True/False."""
    words = re.findall(r'\w+', text.lower())
    bullets = [line for line in text.splitlines() if re.match(r'\s*([-*•]|\d+[.)])\s+', line)]
    return {
        'non_vide': bool(text.strip()),
        'longueur_max_130_mots': word_count(text) <= 130,
        'en_francais': bool(words) and sum(w in FRENCH_WORDS for w in words) / len(words) >= 0.12,
        'cite_la_progression': str(goal.current_progress) in text or str(goal.target_value) in text,
        'au_moins_2_actions': len(bullets) >= 2,
        'sans_promesse_de_points': not BAD_PROMISES.search(text),
    }


def percentile(values, q):
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, round(q * (len(ordered) - 1)))]


class Command(BaseCommand):
    help = 'Évalue le coach IA (latence, tokens, critères de qualité automatiques) sur des objectifs existants.'

    def add_arguments(self, parser):
        parser.add_argument('--limit', type=int, default=10, help='Nombre d’objectifs évalués (défaut : 10).')
        parser.add_argument('--output', default='', help='Fichier JSON où écrire le rapport détaillé.')

    def handle(self, *args, limit, output, **options):
        goals = list(Goal.objects.exclude(status=Goal.Status.ABANDONED).select_related('user').order_by('pk')[:limit])
        if not goals:
            raise CommandError('Aucun objectif en base : lancez d’abord « python manage.py seed_demo_data ».')
        rows, failures = [], []
        for goal in goals:
            try:
                advice = ai.generate_advice(goal)
            except BusinessRuleError as error:
                failures.append({'goal': goal.pk, 'error': error.message})
                self.stdout.write(self.style.ERROR(f'#{goal.pk} échec : {error.message}'))
                continue
            checks = grade(goal, advice.text)
            rows.append({'goal': goal.pk, 'title': goal.title, 'latency_ms': advice.latency_ms,
                         'input_tokens': advice.input_tokens, 'output_tokens': advice.output_tokens,
                         'checks': checks, 'text': advice.text})
            self.stdout.write(f'#{goal.pk} {advice.latency_ms} ms — {sum(checks.values())}/{len(checks)} critères')
        report = self.summarise(rows, failures)
        self.stdout.write(json.dumps(report['summary'], indent=2, ensure_ascii=False))
        if output:
            path = Path(output)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
            self.stdout.write(f'Rapport écrit dans {path}')

    @staticmethod
    def summarise(rows, failures):
        summary = {'objectifs_evalues': len(rows) + len(failures), 'reponses_obtenues': len(rows),
                   'echecs_api': len(failures)}
        if rows:
            latencies = [row['latency_ms'] for row in rows]
            summary.update({
                'latence_ms': {'moyenne': round(statistics.mean(latencies)), 'mediane': round(statistics.median(latencies)),
                               'p95': percentile(latencies, 0.95), 'max': max(latencies)},
                'tokens_entree_moyens': round(statistics.mean(r['input_tokens'] for r in rows)),
                'tokens_sortie_moyens': round(statistics.mean(r['output_tokens'] for r in rows)),
                'taux_de_reussite_par_critere': {
                    name: round(100 * sum(r['checks'][name] for r in rows) / len(rows))
                    for name in rows[0]['checks']
                },
            })
        return {'summary': summary, 'details': rows, 'failures': failures}
