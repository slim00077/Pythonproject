"""Small factories shared by the test suites of every module."""
from datetime import timedelta
from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.utils import timezone
from PIL import Image

from accounts.models import User
from actions.models import ActionSubmission, EcoActionType
from challenges.models import Challenge
from community.models import Event
from core.choices import EcoCategory
from teams.models import Membership, Team

PASSWORD = 'Un-Mot-De-Passe-Solide-2026'


def make_user(username='alice', **extra):
    extra.setdefault('email', f'{username}@example.com')
    extra.setdefault('first_name', username.capitalize())
    return User.objects.create_user(username=username, password=PASSWORD, **extra)


def make_superuser(username='admin'):
    return User.objects.create_superuser(username=username, email=f'{username}@example.com', password=PASSWORD)


def make_team(captain, name='Équipe Test', **extra):
    extra.setdefault('description', 'Équipe utilisée par les tests.')
    team = Team.objects.create(name=name, captain=captain, **extra)
    Membership.objects.create(team=team, user=captain, role=Membership.Role.CAPTAIN)
    return team


def add_member(team, user):
    return Membership.objects.create(team=team, user=user)


def make_action_type(name='Trajet à vélo', category=EcoCategory.TRANSPORT, points=10, **extra):
    extra.setdefault('description', 'Action de test.')
    return EcoActionType.objects.create(name=name, category=category, points=points, **extra)


def make_challenge(creator, title='Défi test', status=Challenge.Status.ACTIVE, category=EcoCategory.TRANSPORT,
                   required_actions=2, reward_points=50, **extra):
    today = timezone.localdate()
    extra.setdefault('start_date', today - timedelta(days=5))
    extra.setdefault('end_date', today + timedelta(days=10))
    return Challenge.objects.create(
        title=title, creator=creator, status=status, category=category, required_actions=required_actions,
        reward_points=reward_points, description='Description du défi.', instructions='Étape 1\nÉtape 2', **extra,
    )


def make_submission(user, action_type, days_ago=1, **extra):
    extra.setdefault('description', 'Action réalisée pour le test.')
    return ActionSubmission.objects.create(
        user=user, action_type=action_type, performed_on=timezone.localdate() - timedelta(days=days_ago), **extra,
    )


def make_event(organizer, title='Événement test', status=Event.Status.PUBLISHED, start_in_hours=72, **extra):
    start = timezone.now() + timedelta(hours=start_in_hours)
    extra.setdefault('end_at', start + timedelta(hours=2))
    extra.setdefault('location', 'Salle polyvalente')
    extra.setdefault('category', EcoCategory.RECYCLING)
    return Event.objects.create(
        title=title, organizer=organizer, status=status, start_at=start, description='Description.', **extra,
    )


def png_upload(name='preuve.png', size=(12, 12)):
    buffer = BytesIO()
    Image.new('RGB', size, color=(34, 197, 94)).save(buffer, format='PNG')
    return SimpleUploadedFile(name, buffer.getvalue(), content_type='image/png')
