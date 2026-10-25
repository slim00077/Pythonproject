"""Activity journal helper shared by every module."""
from teams.models import Membership

from .models import ActivityLog

CURRENT_TEAM = object()


def log_activity(actor, verb, description, team=CURRENT_TEAM, link=''):
    if team is CURRENT_TEAM:
        membership = Membership.objects.filter(user=actor).select_related('team').first()
        team = membership.team if membership else None
    return ActivityLog.objects.create(
        actor=actor, verb=verb, description=description[:255], team=team, link=link or ''
    )
