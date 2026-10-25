from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone

from core.choices import EcoCategory
from core.utils import percent, unique_slugify
from core.validators import UploadToUUID, image_validators

RESERVED_CHALLENGE_SLUGS = {'create', 'mine'}
MAX_REWARD_POINTS = 1000


class Challenge(models.Model):
    class Difficulty(models.TextChoices):
        EASY = 'easy', 'Facile'
        MEDIUM = 'medium', 'Intermédiaire'
        HARD = 'hard', 'Difficile'

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Brouillon'
        PENDING = 'pending', 'En attente de validation'
        ACTIVE = 'active', 'Actif'
        COMPLETED = 'completed', 'Terminé'
        ARCHIVED = 'archived', 'Archivé'

    title = models.CharField('titre', max_length=120)
    slug = models.SlugField('identifiant URL', max_length=140, unique=True, editable=False)
    description = models.TextField('description', max_length=2000)
    category = models.CharField('catégorie environnementale', max_length=20, choices=EcoCategory.choices)
    difficulty = models.CharField('difficulté', max_length=10, choices=Difficulty.choices, default=Difficulty.MEDIUM)
    start_date = models.DateField('date de début')
    end_date = models.DateField('date de fin')
    duration_days = models.PositiveSmallIntegerField(
        'durée recommandée (jours)', default=7, validators=[MinValueValidator(1), MaxValueValidator(365)]
    )
    reward_points = models.PositiveIntegerField(
        'points de récompense', default=50, validators=[MaxValueValidator(MAX_REWARD_POINTS)],
        help_text='Proposition soumise à validation par un responsable des défis.',
    )
    required_actions = models.PositiveSmallIntegerField(
        'actions validées requises', default=3, validators=[MinValueValidator(1), MaxValueValidator(100)],
        help_text='Nombre d’actions écologiques validées, liées au défi, nécessaires pour le réussir.',
    )
    instructions = models.TextField('consignes', max_length=3000)
    image = models.ImageField('image', upload_to=UploadToUUID('challenges'), blank=True, validators=image_validators)
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_challenges',
        verbose_name='créateur',
    )
    status = models.CharField('statut', max_length=20, choices=Status.choices, default=Status.DRAFT)
    review_notes = models.TextField('commentaire de validation', max_length=1000, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='+',
        verbose_name='validé par',
    )
    published_at = models.DateTimeField('publié le', null=True, blank=True)
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL, through='ChallengeParticipation', related_name='joined_challenges',
        verbose_name='participants',
    )
    created_at = models.DateTimeField('créé le', auto_now_add=True)
    updated_at = models.DateTimeField('mis à jour le', auto_now=True)

    class Meta:
        verbose_name = 'défi'
        verbose_name_plural = 'défis'
        ordering = ['-start_date', 'title']
        indexes = [
            models.Index(fields=['status', 'category']),
            models.Index(fields=['start_date', 'end_date']),
        ]
        constraints = [
            models.CheckConstraint(condition=models.Q(end_date__gte=models.F('start_date')), name='challenge_end_after_start'),
            models.CheckConstraint(condition=models.Q(reward_points__lte=MAX_REWARD_POINTS), name='challenge_reward_cap'),
        ]
        permissions = [('review_challenge', 'Peut valider, publier et clôturer les défis')]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(self, self.title, reserved=RESERVED_CHALLENGE_SLUGS)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('challenges:detail', args=[self.slug])

    @property
    def is_joinable(self):
        return self.status == self.Status.ACTIVE and self.end_date >= timezone.localdate()

    @property
    def days_left(self):
        return max(0, (self.end_date - timezone.localdate()).days)

    @property
    def time_progress(self):
        total = (self.end_date - self.start_date).days or 1
        elapsed = (timezone.localdate() - self.start_date).days
        return percent(max(0, elapsed), total)


class ChallengeParticipation(models.Model):
    class Status(models.TextChoices):
        IN_PROGRESS = 'in_progress', 'En cours'
        COMPLETED = 'completed', 'Réussi'
        ABANDONED = 'abandoned', 'Abandonné'

    challenge = models.ForeignKey(Challenge, on_delete=models.CASCADE, related_name='participations', verbose_name='défi')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='challenge_participations',
        verbose_name='participant',
    )
    team = models.ForeignKey(
        'teams.Team', on_delete=models.SET_NULL, null=True, blank=True, related_name='challenge_participations',
        verbose_name='équipe',
    )
    status = models.CharField('statut', max_length=20, choices=Status.choices, default=Status.IN_PROGRESS)
    joined_at = models.DateTimeField('inscrit le', default=timezone.now)
    completed_at = models.DateTimeField('réussi le', null=True, blank=True)

    class Meta:
        verbose_name = 'participation à un défi'
        verbose_name_plural = 'participations aux défis'
        ordering = ['-joined_at']
        indexes = [models.Index(fields=['user', 'status']), models.Index(fields=['team', 'status'])]
        constraints = [
            models.UniqueConstraint(fields=['challenge', 'user'], name='unique_challenge_participation'),
        ]

    def __str__(self):
        return f'{self.user} — {self.challenge}'
