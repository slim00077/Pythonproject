"""Static JavaScript sanity check: a syntax error silently disables every button of a page."""
import shutil
import subprocess
from pathlib import Path

from django.conf import settings
from django.test import SimpleTestCase


class JavaScriptSyntaxTests(SimpleTestCase):
    def test_every_static_script_parses(self):
        node = shutil.which('node')
        if node is None:
            self.skipTest('Node.js is not installed')
        scripts = sorted(Path(settings.BASE_DIR, 'static', 'js').glob('*.js'))
        self.assertTrue(scripts)
        for script in scripts:
            with self.subTest(script=script.name):
                result = subprocess.run([node, '--check', str(script)], capture_output=True, text=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_goal_coach_script_is_complete(self):
        source = Path(settings.BASE_DIR, 'static', 'js', 'goal_coach.js').read_text(encoding='utf-8')
        self.assertTrue(source.rstrip().endswith('})();'), 'goal_coach.js looks truncated')
        for needle in ('function start', 'function poll', "addEventListener('click', start)"):
            self.assertIn(needle, source)
