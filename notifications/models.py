from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone


class Notification(models.Model):
    class Kind(models.TextChoices):
        TEAM = 'team', 'Équipe'
        CHALLENGE = 'challenge', 'Défi'
        ACTION = 'action', 'Action écologique'
        POINTS = 'points', 'Points'
        BADGE = 'badge', 'Badge'
        GOAL = 'goal', 'Objectif'
        EVENT = 'event', 'Événement'
        LEADERBOARD = 'leaderboard', 'Classement'
        SYSTEM = 'system', 'Système'

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications',
        verbose_name='destinataire',
    )
    kind = models.CharField('type', max_length=20, choices=Kind.choices, default=Kind.SYSTEM)
    title = models.CharField('titre', max_length=140)
    message = models.TextField('message', max_length=600, blank=True)
    link = models.CharField('lien interne', max_length=255, blank=True)
    is_read = models.BooleanField('lue', default=False)
    read_at = models.DateTimeField('lue le', null=True, blank=True)
    created_at = models.DateTimeField('créée le', default=timezone.now)

    class Meta:
        verbose_name = 'notification'
        verbose_name_plural = 'notifications'
        ordering = ['-created_at']
        indexes = [models.Index(fields=['recipient', 'is_read', 'created_at'])]

    def __str__(self):
        return f'{self.title} → {self.recipient}'

    def get_absolute_url(self):
        return reverse('notifications:detail', args=[self.pk])

    @property
    def icon(self):
        return {
            'team': 'users', 'challenge': 'flag', 'action': 'leaf', 'points': 'zap', 'badge': 'award',
            'goal': 'target', 'event': 'calendar', 'leaderboard': 'trophy',
        }.get(self.kind, 'bell')

    def mark_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save(update_fields=['is_read', 'read_at'])


class NotificationPreference(models.Model):
    """Which kinds of in-app notifications a user wants to receive."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notification_preference',
        verbose_name='utilisateur',
    )
    team = models.BooleanField('Vie de mon équipe', default=True)
    challenge = models.BooleanField('Défis', default=True)
    action = models.BooleanField('Validation de mes actions', default=True)
    points = models.BooleanField('Points gagnés', default=True)
    badge = models.BooleanField('Badges débloqués', default=True)
    goal = models.BooleanField('Progression de mes objectifs', default=True)
    event = models.BooleanField('Événements et campagnes', default=True)
    leaderboard = models.BooleanField('Paliers du classement', default=True)
    updated_at = models.DateTimeField('mis à jour le', auto_now=True)

    KIND_FIELDS = ['team', 'challenge', 'action', 'points', 'badge', 'goal', 'event', 'leaderboard']

    class Meta:
        verbose_name = 'préférence de notification'
        verbose_name_plural = 'préférences de notification'

    def __str__(self):
        return f'Préférences de {self.user}'

    def allows(self, kind):
        if kind in self.KIND_FIELDS:
            return getattr(self, kind)
        return True
