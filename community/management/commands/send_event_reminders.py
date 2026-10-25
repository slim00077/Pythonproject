from django.core.management.base import BaseCommand

from community.services import send_due_reminders


class Command(BaseCommand):
    help = 'Envoie une notification de rappel aux participants des événements qui commencent bientôt.'

    def handle(self, *args, **options):
        sent = send_due_reminders()
        self.stdout.write(self.style.SUCCESS(f'{sent} rappel(s) envoyé(s).'))
