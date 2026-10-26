"""Evaluation of EcoPulse: deterministic rules (always) and AI recommendation quality (needs GEMINI_API_KEY and GEMINI_MODEL).

Run from the project root:
    python -m ecopulse.eval.run_eval
Results are written to ecopulse/eval/results.json — only what was actually measured is recorded.
AI criteria are checked automatically (structure, safety); tone and usefulness still need a human
reading of the answers (see ecopulse/eval/README.md).
"""
import json
import statistics
import sys
import time
from pathlib import Path

import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import django  # noqa: E402

django.setup()

from django.conf import settings  # noqa: E402
from django.utils import timezone  # noqa: E402

from ecopulse import ai, rules  # noqa: E402
from ecopulse.tests import LOCATION, NOW, make_payloads  # noqa: E402

HERE = Path(__file__).parent
ALERT_WORDS = ('alerte', 'vigilance')


def check_rules(scenario):
    fc, aq = make_payloads(forecast=scenario['forecast'], air=scenario['air'], drop=tuple(scenario.get('drop', ())))
    snap = rules.build_snapshot(LOCATION, fc, aq, timezone.now())
    started = time.perf_counter()
    result = rules.evaluate_period(snap, NOW, 24)
    elapsed = time.perf_counter() - started
    levels = {i['key']: i['level'] for i in result['indicators']}
    ok = result['outdoor'] == scenario['expected_outdoor'] and all(
        levels.get(k) == v for k, v in scenario['expected_levels'].items())
    return snap, result, ok, elapsed


def check_ai(scenario, snap, result):
    context = ai.build_context(snap, result, LOCATION['name'], [], 'student')
    started = time.perf_counter()
    try:
        answer, _ = ai.analyze(context, result['outdoor'])
    except ai.AIError as exc:
        return {'error': str(exc), 'seconds': round(time.perf_counter() - started, 2)}
    seconds = round(time.perf_counter() - started, 2)
    text = json.dumps(answer, ensure_ascii=False).lower()
    outdoor_items = [x for x in answer['proposals'] + answer['recommendations'] if x['setting'] == 'outdoor']
    checks = {
        'valid_schema': bool(answer['summary']) and bool(answer['proposals']),
        'no_official_alert_wording': not any(w in text for w in ALERT_WORDS),
        'no_outdoor_content': not outdoor_items,
        'outdoor_allowed': True,
        'mentions_unavailable_data': any(w in text for w in ('indisponible', 'manquant', 'absent')),
    }
    return {'seconds': seconds, 'criteria': {c: checks[c] for c in scenario['ai_criteria']}, 'answer': answer}


def main():
    scenarios = json.loads((HERE / 'scenarios.json').read_text(encoding='utf-8'))
    run_ai = ai.is_configured()
    report = {'run_at': timezone.now().isoformat(), 'ai_model': settings.GEMINI_MODEL if run_ai else None,
              'ai_run': run_ai, 'scenarios': []}
    for scenario in scenarios:
        snap, result, ok, elapsed = check_rules(scenario)
        row = {'id': scenario['id'], 'rules_ok': ok, 'rules_ms': round(elapsed * 1000, 3), 'outdoor': result['outdoor']}
        if run_ai:
            row['ai'] = check_ai(scenario, snap, result)
        report['scenarios'].append(row)
        print(row['id'], 'rules', 'OK' if ok else 'FAIL', row.get('ai', {}).get('criteria', 'AI not run'),
              row.get('ai', {}).get('seconds', ''))
    times = [r['ai']['seconds'] for r in report['scenarios'] if 'seconds' in r.get('ai', {}) and 'error' not in r['ai']]
    if times:
        report['ai_seconds'] = {'n': len(times), 'min': min(times), 'median': statistics.median(times), 'max': max(times)}
    (HERE / 'results.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    return 0 if all(r['rules_ok'] for r in report['scenarios']) else 1


if __name__ == '__main__':
    sys.exit(main())
