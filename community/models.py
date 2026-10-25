from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone

from core.choices import Audience, EcoCategory
from core.utils import percent, unique_slugify

RESERVED_EVENT_SLUGS = {'create', 'mine'}


class Event(models.Model):
    class Kind(models.TextChoices):
        EVENT = 'event', 'Événement'
        CAMPAIGN = 'campaign', 'Campagne'

    class Format(models.TextChoices):
        ON_SITE = 'on_site', 'Présentiel'
        ONLINE = 'online', 'En ligne'
        HYBRID = 'hybrid', 'Hybride'

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Brouillon'
        PENDING = 'pending', 'En attente de validation'
        PUBLISHED = 'published', 'Publié'
        CANCELLED = 'cancelled', 'Annulé'
        COMPLETED = 'completed', 'Terminé'

    title = models.CharField('titre', max_length=120)
    slug = models.SlugField('identifiant URL', max_length=140, unique=True, editable=False)
    kind = models.CharField('type', max_length=10, choices=Kind.choices, default=Kind.EVENT)
    description = models.TextField('description', max_length=3000)
    category = models.CharField('catégorie', max_length=20, choices=EcoCategory.choices)
    format = models.CharField('format', max_length=10, choices=Format.choices, default=Format.ON_SITE)
    location = models.CharField('lieu', max_length=160, blank=True)
    online_url = models.URLField('lien de connexion', blank=True)
    start_at = models.DateTimeField('début')
    end_at = models.DateTimeField('fin')
    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='organized_events',
        verbose_name='organisateur',
    )
    organization = models.ForeignKey(
        'organizations.Organization', on_delete=models.SET_NULL, null=True, blank=True, related_name='events',
        verbose_name='organisation',
    )
    registration_deadline = models.DateTimeField(
        'date limite d’inscription', null=True, blank=True,
        help_text='Laisser vide pour autoriser les inscriptions jusqu’au début de l’événement.',
    )
    target_audience = models.CharField('public visé', max_length=20, choices=Audience.choices, default=Audience.ALL)
    capacity = models.PositiveIntegerField(
        'capacité maximale', null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(10000)],
        help_text='Laisser vide pour un nombre de places illimité.',
    )
    participation_goal = models.PositiveIntegerField(
        'objectif de participants', null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(10000)],
        help_text='Sert à afficher la progression d’une campagne.',
    )
    actual_co2_saved_kg = models.DecimalField(
        'CO₂ réellement économisé (kg)', max_digits=10, decimal_places=3, null=True, blank=True,
        validators=[MinValueValidator(0)],
        help_text='Résultat réel saisi après une campagne terminée.',
    )
    status = models.CharField('statut', max_length=20, choices=Status.choices, default=Status.DRAFT)
    review_notes = models.TextField('commentaire de validation', max_length=1000, blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='+',
        verbose_name='validé par',
    )
    published_at = models.DateTimeField('publié le', null=True, blank=True)
    participants = models.ManyToManyField(
        settings.AUTH_USER_MODEL, through='EventParticipation', related_name='joined_events',
        verbose_name='participants',
    )
    created_at = models.DateTimeField('créé le', auto_now_add=True)
    updated_at = models.DateTimeField('mis à jour le', auto_now=True)

    class Meta:
        verbose_name = 'événement ou campagne'
        verbose_name_plural = 'événements et campagnes'
        ordering = ['start_at']
        indexes = [models.Index(fields=['status', 'start_at'])]
        constraints = [
            models.CheckConstraint(condition=models.Q(end_at__gte=models.F('start_at')), name='event_end_after_start'),
        ]
        permissions = [('review_event', 'Peut valider et publier les événements')]

    def __str__(self):
        return self.title

    def clean(self):
        errors = {}
        if self.format != self.Format.ONLINE and not self.location:
            errors['location'] = 'Indiquez un lieu pour un événement en présentiel ou hybride.'
        if self.format != self.Format.ON_SITE and not self.online_url:
            errors['online_url'] = 'Indiquez le lien de connexion pour un événement en ligne ou hybride.'
        if self.start_at and self.end_at and self.end_at < self.start_at:
            errors['end_at'] = 'La fin doit être postérieure au début.'
        if self.registration_deadline and self.start_at and self.registration_deadline > self.start_at:
            errors['registration_deadline'] = 'La date limite d’inscription doit précéder le début de l’événement.'
        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(self, self.title, reserved=RESERVED_EVENT_SLUGS)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('community:detail', args=[self.slug])

    @property
    def participant_count(self):
        return self.participations.count()

    @property
    def is_full(self):
        return self.capacity is not None and self.participant_count >= self.capacity

    @property
    def has_started(self):
        return self.start_at <= timezone.now()

    @property
    def has_ended(self):
        return self.end_at < timezone.now()

    @property
    def registration_closed(self):
        return bool(self.registration_deadline and self.registration_deadline < timezone.now())

    @property
    def is_joinable(self):
        return (
            self.status == self.Status.PUBLISHED and not self.has_ended and not self.is_full
            and not self.registration_closed
        )

    @property
    def participation_progress(self):
        target = self.participation_goal or self.capacity
        return percent(self.participant_count, target) if target else None

    @property
    def time_progress(self):
        total = (self.end_at - self.start_at).total_seconds() or 1
        elapsed = (timezone.now() - self.start_at).total_seconds()
        return percent(max(0, elapsed), total)


class CampaignImpactFactor(models.Model):
    category = models.CharField('catégorie', max_length=20, choices=EcoCategory.choices, unique=True)
    co2_kg_per_participant_day = models.DecimalField(
        'CO₂ (kg par participant-jour)', max_digits=8, decimal_places=4,
        validators=[MinValueValidator(0)],
    )
    points_per_participant_day = models.PositiveSmallIntegerField(
        'points par participant-jour', validators=[MaxValueValidator(100)],
    )
    source = models.CharField('source / nature du facteur', max_length=255)
    methodology = models.TextField('méthodologie et limites', max_length=1000)
    is_active = models.BooleanField('actif', default=True)
    updated_at = models.DateTimeField('mis à jour le', auto_now=True)

    class Meta:
        verbose_name = 'facteur d’impact de campagne'
        verbose_name_plural = 'facteurs d’impact des campagnes'
        ordering = ['category']

    def __str__(self):
        return self.get_category_display()


class EventParticipation(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='participations', verbose_name='événement')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='event_participations',
        verbose_name='participant',
    )
    team = models.ForeignKey(
        'teams.Team', on_delete=models.SET_NULL, null=True, blank=True, related_name='event_participations',
        verbose_name='équipe',
    )
    joined_at = models.DateTimeField('inscrit le', default=timezone.now)
    reminder_sent = models.BooleanField('rappel envoyé', default=False)
    attended = models.BooleanField(
        'présence confirmée', null=True, blank=True, default=None,
        help_text='Laisser à confirmer tant que la présence n’a pas été vérifiée.',
    )

    class Meta:
        verbose_name = 'participation à un événement'
        verbose_name_plural = 'participations aux événements'
        ordering = ['-joined_at']
        constraints = [models.UniqueConstraint(fields=['event', 'user'], name='unique_event_participation')]

    def __str__(self):
        return f'{self.user} — {self.event}'
