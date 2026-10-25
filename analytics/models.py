from django.conf import settings
from django.db import models
from django.utils import timezone


class ActivityLog(models.Model):
    """Append-only audit trail of what happened in the application."""

    class Verb(models.TextChoices):
        TEAM_CREATED = 'team_created', 'Équipe créée'
        TEAM_UPDATED = 'team_updated', 'Équipe modifiée'
        TEAM_DELETED = 'team_deleted', 'Équipe supprimée'
        TEAM_JOINED = 'team_joined', 'Équipe rejointe'
        TEAM_LEFT = 'team_left', 'Équipe quittée'
        MEMBER_REMOVED = 'member_removed', 'Membre retiré'
        CAPTAIN_CHANGED = 'captain_changed', 'Capitaine changé'
        CHALLENGE_CREATED = 'challenge_created', 'Défi créé'
        CHALLENGE_SUBMITTED = 'challenge_submitted', 'Défi soumis à validation'
        CHALLENGE_PUBLISHED = 'challenge_published', 'Défi publié'
        CHALLENGE_REJECTED = 'challenge_rejected', 'Défi renvoyé en brouillon'
        CHALLENGE_STATUS = 'challenge_status', 'Statut de défi modifié'
        CHALLENGE_JOINED = 'challenge_joined', 'Défi rejoint'
        CHALLENGE_LEFT = 'challenge_left', 'Défi abandonné'
        CHALLENGE_COMPLETED = 'challenge_completed', 'Défi réussi'
        ACTION_SUBMITTED = 'action_submitted', 'Action déclarée'
        ACTION_APPROVED = 'action_approved', 'Action validée'
        ACTION_REJECTED = 'action_rejected', 'Action refusée'
        ACTION_REVOKED = 'action_revoked', 'Validation annulée'
        GOAL_CREATED = 'goal_created', 'Objectif créé'
        GOAL_COMPLETED = 'goal_completed', 'Objectif atteint'
        BADGE_UNLOCKED = 'badge_unlocked', 'Badge débloqué'
        POINTS_ADJUSTED = 'points_adjusted', 'Correction de points'
        EVENT_CREATED = 'event_created', 'Événement créé'
        EVENT_PUBLISHED = 'event_published', 'Événement publié'
        EVENT_STATUS = 'event_status', 'Statut d’événement modifié'
        EVENT_JOINED = 'event_joined', 'Inscription à un événement'
        EVENT_LEFT = 'event_left', 'Désinscription d’un événement'
        ROLE_CHANGED = 'role_changed', 'Rôles modifiés'

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='activities', verbose_name='auteur'
    )
    team = models.ForeignKey(
        'teams.Team', on_delete=models.SET_NULL, null=True, blank=True, related_name='activities',
        verbose_name='équipe',
    )
    verb = models.CharField('type', max_length=30, choices=Verb.choices)
    description = models.CharField('description', max_length=255)
    link = models.CharField('lien', max_length=255, blank=True)
    created_at = models.DateTimeField('date', default=timezone.now, db_index=True)

    class Meta:
        verbose_name = 'activité'
        verbose_name_plural = 'journal d’activité'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['actor', 'created_at']),
            models.Index(fields=['team', 'created_at']),
        ]
        permissions = [('view_reports', 'Peut consulter les rapports d’engagement')]

    def __str__(self):
        return f'{self.created_at:%d/%m/%Y} — {self.description}'

    @property
    def icon(self):
        prefix = self.verb.split('_')[0]
        return {
            'team': 'users', 'member': 'user-minus', 'captain': 'crown', 'challenge': 'flag',
            'action': 'leaf', 'goal': 'target', 'badge': 'award', 'points': 'zap', 'event': 'calendar',
            'role': 'shield',
        }.get(prefix, 'activity')
