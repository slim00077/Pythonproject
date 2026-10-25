"""Health probe used by Docker, CI and the hosting platform."""
import os
import secrets
import subprocess
import sys
from pathlib import Path
from unittest import mock

from django.conf import settings
from django.test import SimpleTestCase, TestCase
from django.urls import reverse


class HealthTests(TestCase):
    def test_healthy_when_database_answers(self):
        response = self.client.get(reverse('core:health'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'status': 'ok', 'database': 'up'})

    def test_public_and_cheap(self):
        # No login, no redirect, no template rendering: a probe must work for an anonymous caller.
        with self.assertNumQueries(1):
            self.assertEqual(self.client.get('/healthz/').status_code, 200)

    def test_unavailable_when_database_is_down(self):
        with mock.patch('core.views.connection.cursor', side_effect=Exception('db down')):
            response = self.client.get('/healthz/')
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.json()['database'], 'down')


class ProductionSettingsTests(SimpleTestCase):
    """Boot Django with production-like environment variables in a separate process."""

    def run_check(self, **env):
        base = {**os.environ, 'DJANGO_DEBUG': 'False', 'DJANGO_SECRET_KEY': secrets.token_urlsafe(60), 'DB_ENGINE': 'sqlite',
                'DJANGO_ALLOWED_HOSTS': 'example.com', 'SQLITE_NAME': ':memory:', 'DJANGO_SECURE_COOKIES': 'True'}
        base.update(env)
        return subprocess.run([sys.executable, 'manage.py', 'check', '--deploy', '--fail-level', 'ERROR'],
                              cwd=Path(settings.BASE_DIR), env=base, capture_output=True, text=True, timeout=120)

    def test_production_boot_without_secret_key_is_refused(self):
        result = self.run_check(DJANGO_SECRET_KEY='')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('DJANGO_SECRET_KEY', result.stderr)

    def test_production_boot_with_secret_key_passes_deploy_check(self):
        result = self.run_check(DJANGO_BEHIND_PROXY='True', DJANGO_HSTS_SECONDS='3600', DJANGO_SECURE_SSL_REDIRECT='True')
        self.assertEqual(result.returncode, 0, result.stderr)
        output = result.stderr + result.stdout
        # HSTS, HTTPS redirect, secure cookies, secret key strength: all configured. (W005/W021, HSTS subdomains
        # and preload, are deliberately left off: we do not control every subdomain of the hosting domain.)
        for code in ('W004', 'W008', 'W009', 'W012', 'W016', 'W018', 'W020'):
            self.assertNotIn(f'security.{code}', output)

    def test_render_hostname_is_trusted_automatically(self):
        code = ('import django,os;os.environ["DJANGO_SETTINGS_MODULE"]="config.settings";'
                'from django.conf import settings;print(settings.ALLOWED_HOSTS, settings.CSRF_TRUSTED_ORIGINS)')
        env = {**os.environ, 'DJANGO_DEBUG': 'True', 'RENDER_EXTERNAL_HOSTNAME': 'eco.onrender.com'}
        result = subprocess.run([sys.executable, '-c', code], cwd=Path(settings.BASE_DIR), env=env,
                                capture_output=True, text=True, timeout=60)
        self.assertIn('eco.onrender.com', result.stdout)
        self.assertIn('https://eco.onrender.com', result.stdout)
