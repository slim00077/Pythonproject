from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from core.choices import EcoCategory
from core.icons import BADGE_ICON_CHOICES
from core.utils import unique_slugify


class PointTransaction(models.Model):
    """Append-only points ledger. Every score in EcoTeams is a sum of these rows.

    ``reference`` is unique, so the same approved action or challenge
    completion can never be rewarded twice.
    """

    class Reason(models.TextChoices):
        ACTION_APPROVED = 'action_approved', 'Action écologique validée'
        CHALLENGE_COMPLETED = 'challenge_completed', 'Défi réussi'
        ACTION_REVOKED = 'action_revoked', 'Annulation d’une validation'
        MANUAL_ADJUSTMENT = 'manual_adjustment', 'Correction administrative'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='point_transactions',
        verbose_name='utilisateur',
    )
    team = models.ForeignKey(
        'teams.Team', on_delete=models.SET_NULL, null=True, blank=True, related_name='point_transactions',
        verbose_name='équipe au moment du gain',
    )
    amount = models.IntegerField('points')
    reason = models.CharField('motif', max_length=30, choices=Reason.choices)
    description = models.CharField('description', max_length=255)
    submission = models.ForeignKey(
        'actions.ActionSubmission', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='point_transactions', verbose_name='action liée',
    )
    challenge = models.ForeignKey(
        'challenges.Challenge', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='point_transactions', verbose_name='défi lié',
    )
    reference = models.CharField('référence unique', max_length=120, unique=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='+',
        verbose_name='saisi par',
    )
    created_at = models.DateTimeField('date', default=timezone.now, db_index=True)

    class Meta:
        verbose_name = 'transaction de points'
        verbose_name_plural = 'registre des points'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['team', 'created_at']),
        ]
        constraints = [
            models.CheckConstraint(condition=~models.Q(amount=0), name='point_transaction_non_zero'),
        ]
        permissions = [('adjust_points', 'Peut enregistrer des corrections de points')]

    def __str__(self):
        sign = '+' if self.amount > 0 else ''
        return f'{sign}{self.amount} pts — {self.user} ({self.get_reason_display()})'

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise ValidationError('Le registre des points est en lecture seule : créez une correction.')
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError('Le registre des points est en lecture seule : créez une correction.')


class Badge(models.Model):
    class Rule(models.TextChoices):
        ACTIONS_TOTAL = 'actions_total', 'Nombre d’actions validées'
        CATEGORY_ACTIONS = 'category_actions', 'Actions validées dans une catégorie'
        POINTS_TOTAL = 'points_total', 'Total de points'
        STREAK_DAYS = 'streak_days', 'Jours consécutifs avec une action validée'
        CHALLENGES_COMPLETED = 'challenges_completed', 'Défis réussis'
        GOALS_COMPLETED = 'goals_completed', 'Objectifs personnels atteints'
        EVENTS_JOINED = 'events_joined', 'Inscriptions à des événements'
        TEAM_RANK = 'team_rank', 'Rang de l’équipe au classement (inférieur ou égal au seuil)'

    class Tone(models.TextChoices):
        LIME = 'lime', 'Citron vert'
        EMERALD = 'emerald', 'Émeraude'
        CYAN = 'cyan', 'Cyan'
        GOLD = 'gold', 'Or'

    name = models.CharField('nom', max_length=80, unique=True)
    slug = models.SlugField('identifiant', max_length=90, unique=True, editable=False)
    description = models.CharField('description', max_length=255)
    icon = models.CharField('icône', max_length=30, choices=BADGE_ICON_CHOICES, default='award')
    tone = models.CharField('couleur', max_length=10, choices=Tone.choices, default=Tone.LIME)
    rule = models.CharField('condition de déblocage', max_length=30, choices=Rule.choices)
    category = models.CharField(
        'catégorie', max_length=20, choices=EcoCategory.choices, blank=True,
        help_text='Uniquement pour la condition « Actions validées dans une catégorie ».',
    )
    threshold = models.PositiveIntegerField('seuil', validators=[MinValueValidator(1)])
    is_active = models.BooleanField('actif', default=True)
    created_at = models.DateTimeField('créé le', auto_now_add=True)
    updated_at = models.DateTimeField('mis à jour le', auto_now=True)

    class Meta:
        verbose_name = 'badge'
        verbose_name_plural = 'badges'
        ordering = ['rule', 'threshold']
        constraints = [
            models.CheckConstraint(condition=models.Q(threshold__gte=1), name='badge_threshold_positive'),
        ]

    def __str__(self):
        return self.name

    def clean(self):
        if self.rule == self.Rule.CATEGORY_ACTIONS and not self.category:
            raise ValidationError({'category': 'Choisissez la catégorie concernée par ce badge.'})
        if self.rule != self.Rule.CATEGORY_ACTIONS:
            self.category = ''

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(self, self.name)
        super().save(*args, **kwargs)


class UserBadge(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='badges_earned', verbose_name='utilisateur'
    )
    badge = models.ForeignKey(Badge, on_delete=models.PROTECT, related_name='awards', verbose_name='badge')
    awarded_at = models.DateTimeField('obtenu le', default=timezone.now)

    class Meta:
        verbose_name = 'badge obtenu'
        verbose_name_plural = 'badges obtenus'
        ordering = ['-awarded_at']
        constraints = [models.UniqueConstraint(fields=['user', 'badge'], name='unique_user_badge')]

    def __str__(self):
        return f'{self.badge} — {self.user}'
