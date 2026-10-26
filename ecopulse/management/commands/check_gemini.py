"""Small live check of the Gemini configuration: ``python manage.py check_gemini`` (one tiny request)."""
import time

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from ecopulse import ai


class Command(BaseCommand):
    help = 'Envoie une requête minimale à Gemini pour vérifier GEMINI_API_KEY et GEMINI_MODEL.'

    def handle(self, *args, **options):
        if not settings.GEMINI_API_KEY or not settings.GEMINI_MODEL:
            raise CommandError('Définissez GEMINI_API_KEY et GEMINI_MODEL dans le fichier .env (voir README).')
        started = time.monotonic()
        try:
            text, reply, _elapsed = ai.call_model(
                lambda: ai.create_message('Réponds uniquement par un objet JSON.', 'Réponds {"ok": true}.', 1000),
                label='check_gemini')
        except ai.AIError as exc:
            raise CommandError(f'Échec : {exc} (détails dans les journaux du serveur)') from exc
        self.stdout.write(self.style.SUCCESS(
            f'OK : modèle {settings.GEMINI_MODEL}, réponse en {time.monotonic() - started:.2f} s, '
            f'{reply.output_tokens} jetons de sortie.'))
