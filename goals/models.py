from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone

from core.choices import EcoCategory
from core.utils import percent


class Goal(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'En cours'
        COMPLETED = 'completed', 'Atteint'
        ABANDONED = 'abandoned', 'Abandonné'

    class TrackingMode(models.TextChoices):
        MANUAL = 'manual', 'Suivi manuel'
        ACTIONS = 'actions', 'Automatique — actions validées'
        POINTS = 'points', 'Automatique — points gagnés'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='goals', verbose_name='utilisateur'
    )
    title = models.CharField('titre', max_length=120)
    description = models.TextField('description', max_length=1000, blank=True)
    category = models.CharField(
        'catégorie', max_length=20, choices=EcoCategory.choices, blank=True,
        help_text='Laisser vide pour suivre toutes les catégories.',
    )
    tracking_mode = models.CharField(
        'mode de suivi', max_length=10, choices=TrackingMode.choices, default=TrackingMode.MANUAL
    )
    target_value = models.PositiveIntegerField(
        'valeur cible', validators=[MinValueValidator(1), MaxValueValidator(100000)]
    )
    current_progress = models.PositiveIntegerField('progression actuelle', default=0)
    unit = models.CharField('unité', max_length=30, default='actions')
    start_date = models.DateField('date de début', default=timezone.localdate)
    deadline = models.DateField('échéance')
    status = models.CharField('statut', max_length=20, choices=Status.choices, default=Status.ACTIVE)
    completed_at = models.DateTimeField('atteint le', null=True, blank=True)
    created_at = models.DateTimeField('créé le', auto_now_add=True)
    updated_at = models.DateTimeField('mis à jour le', auto_now=True)

    class Meta:
        verbose_name = 'objectif personnel'
        verbose_name_plural = 'objectifs personnels'
        ordering = ['status', 'deadline']
        indexes = [models.Index(fields=['user', 'status'])]
        constraints = [
            models.CheckConstraint(condition=models.Q(deadline__gte=models.F('start_date')), name='goal_deadline_after_start'),
            models.CheckConstraint(condition=models.Q(target_value__gte=1), name='goal_target_positive'),
        ]

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('goals:detail', args=[self.pk])

    @property
    def progress_percent(self):
        return percent(self.current_progress, self.target_value)

    @property
    def is_automatic(self):
        return self.tracking_mode != self.TrackingMode.MANUAL

    @property
    def is_overdue(self):
        return self.status == self.Status.ACTIVE and self.deadline < timezone.localdate()

    @property
    def days_left(self):
        return (self.deadline - timezone.localdate()).days


class GoalAdvice(models.Model):
    """One request to the AI goal coach, with its outcome and measured performance."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'En cours'
        DONE = 'done', 'Terminé'
        FAILED = 'failed', 'Échec'

    goal = models.ForeignKey(Goal, on_delete=models.CASCADE, related_name='advices', verbose_name='objectif')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='goal_advices', verbose_name='utilisateur'
    )
    status = models.CharField('statut', max_length=10, choices=Status.choices, default=Status.PENDING)
    content = models.TextField('conseil', blank=True)
    error = models.CharField('message d’erreur', max_length=255, blank=True)
    model_name = models.CharField('modèle', max_length=60, blank=True)
    latency_ms = models.PositiveIntegerField('durée de l’appel (ms)', null=True, blank=True)
    input_tokens = models.PositiveIntegerField('tokens en entrée', null=True, blank=True)
    output_tokens = models.PositiveIntegerField('tokens en sortie', null=True, blank=True)
    helpful = models.BooleanField('jugé utile', null=True, blank=True)
    created_at = models.DateTimeField('demandé le', auto_now_add=True)
    finished_at = models.DateTimeField('terminé le', null=True, blank=True)

    class Meta:
        verbose_name = 'conseil du coach IA'
        verbose_name_plural = 'conseils du coach IA'
        ordering = ['-created_at']
        indexes = [models.Index(fields=['user', 'created_at'])]

    def __str__(self):
        return f'Conseil #{self.pk} — {self.goal}'


class GoalProposalRun(models.Model):
    """One use of the AI Goal Studio: what was asked, what was proposed, what the user kept."""

    class Status(models.TextChoices):
        DONE = 'done', 'Terminé'
        FAILED = 'failed', 'Échec'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='goal_proposal_runs', verbose_name='utilisateur'
    )
    ambition = models.CharField('ambition saisie', max_length=400)
    status = models.CharField('statut', max_length=10, choices=Status.choices, default=Status.DONE)
    error = models.CharField('message d’erreur', max_length=255, blank=True)
    proposals = models.JSONField('propositions valides', default=list, blank=True)
    accepted = models.JSONField('propositions créées', default=list, blank=True)
    total_count = models.PositiveSmallIntegerField('propositions renvoyées par l’IA', default=0)
    valid_count = models.PositiveSmallIntegerField('propositions valides', default=0)
    model_name = models.CharField('modèle', max_length=60, blank=True)
    latency_ms = models.PositiveIntegerField('durée de l’appel (ms)', null=True, blank=True)
    input_tokens = models.PositiveIntegerField('tokens en entrée', null=True, blank=True)
    output_tokens = models.PositiveIntegerField('tokens en sortie', null=True, blank=True)
    created_at = models.DateTimeField('généré le', auto_now_add=True)

    class Meta:
        verbose_name = 'génération du studio d’objectifs IA'
        verbose_name_plural = 'générations du studio d’objectifs IA'
        ordering = ['-created_at']
        indexes = [models.Index(fields=['user', 'created_at'])]

    def __str__(self):
        return f'Studio #{self.pk} — {self.ambition[:40]}'
