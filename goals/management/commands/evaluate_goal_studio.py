"""Measure the AI Goal Studio on a fixed set of ambitions: validity, structure, latency, tokens.

    python manage.py evaluate_goal_studio --username demo_amina --output reports/studio_eval.json

Nothing is written to the database (no run is stored, the daily limit is not consumed).
"""
import json
import statistics
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from accounts.models import User
from core.exceptions import BusinessRuleError
from goals import ai, studio

AMBITIONS = [
    'Je veux réduire ma consommation d’énergie à la maison avant la fin du trimestre',
    'Je voudrais me déplacer davantage à vélo et moins en voiture',
    'Je veux arrêter de gaspiller la nourriture',
    'Je veux mieux trier mes déchets et recycler plus',
    'Consommer moins d’eau sous la douche',
    'Acheter moins de vêtements neufs cette année',
    'Je veux motiver mon équipe à faire un geste écologique chaque jour',
    'aider la planète',
]


def grade(proposals, total):
    """Objective rubric on the proposals that survived ``GoalForm`` validation."""
    data = [p['data'] for p in proposals]
    return {
        'json_exploitable': True,
        'trois_propositions_renvoyees': total == studio.PROPOSAL_COUNT,
        'toutes_valides_pour_le_formulaire': len(proposals) == total and total > 0,
        'difficulte_facile_moyen_ambitieux': [p['difficulty'] for p in proposals] == list(studio.DIFFICULTIES),
        'titres_distincts': len({d['title'].lower() for d in data}) == len(data),
        'cibles_croissantes': all(a['target_value'] <= b['target_value'] for a, b in zip(data, data[1:])
                                  if a['tracking_mode'] == b['tracking_mode']),
        'suivi_automatique_privilegie': any(d['tracking_mode'] != 'manual' for d in data),
        'premier_pas_renseigne': all(p['first_step'] for p in proposals),
    }


class Command(BaseCommand):
    help = 'Évalue le studio d’objectifs IA (validité, structure, latence, tokens) sur 8 ambitions types.'

    def add_arguments(self, parser):
        parser.add_argument('--username', default='demo_amina', help='Compte dont l’historique sert de contexte.')
        parser.add_argument('--output', default='', help='Fichier JSON où écrire le rapport détaillé.')

    def handle(self, *args, username, output, **options):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            raise CommandError(f'Utilisateur « {username} » introuvable (lancez seed_demo_data).')
        rows, failures = [], []
        for ambition in AMBITIONS:
            try:
                result = ai.complete(studio.SYSTEM_PROMPT, studio.build_prompt(user, ambition),
                                     schema=studio.SCHEMA, max_tokens=3000)
                proposals, total = studio.parse_proposals(result.text)
            except BusinessRuleError as error:
                failures.append({'ambition': ambition, 'error': error.message})
                self.stdout.write(self.style.ERROR(f'« {ambition[:40]} » échec : {error.message}'))
                continue
            checks = grade(proposals, total)
            rows.append({'ambition': ambition, 'latency_ms': result.latency_ms, 'input_tokens': result.input_tokens,
                         'output_tokens': result.output_tokens, 'valid': len(proposals), 'total': total,
                         'checks': checks, 'proposals': [p['data'] | {'difficulty': p['difficulty']} for p in proposals]})
            self.stdout.write(f'« {ambition[:40]} » {result.latency_ms} ms — {len(proposals)}/{total} valides, '
                              f'{sum(checks.values())}/{len(checks)} critères')
        report = self.summarise(rows, failures)
        self.stdout.write(json.dumps(report['summary'], indent=2, ensure_ascii=False))
        if output:
            path = Path(output)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding='utf-8')
            self.stdout.write(f'Rapport écrit dans {path}')

    @staticmethod
    def summarise(rows, failures):
        summary = {'ambitions_evaluees': len(rows) + len(failures), 'reponses_obtenues': len(rows),
                   'echecs_api': len(failures)}
        if rows:
            latencies = sorted(r['latency_ms'] for r in rows)
            valid, total = sum(r['valid'] for r in rows), sum(r['total'] for r in rows)
            summary.update({
                'propositions_valides_sur_renvoyees': f'{valid}/{total}',
                'taux_de_validite_pct': round(100 * valid / total) if total else 0,
                'latence_ms': {'moyenne': round(statistics.mean(latencies)), 'mediane': round(statistics.median(latencies)),
                               'p95': latencies[min(len(latencies) - 1, round(0.95 * (len(latencies) - 1)))],
                               'max': latencies[-1]},
                'tokens_entree_moyens': round(statistics.mean(r['input_tokens'] for r in rows)),
                'tokens_sortie_moyens': round(statistics.mean(r['output_tokens'] for r in rows)),
                'taux_de_reussite_par_critere': {
                    name: round(100 * sum(r['checks'][name] for r in rows) / len(rows)) for name in rows[0]['checks']
                },
            })
        return {'summary': summary, 'details': rows, 'failures': failures}
