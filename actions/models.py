from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone

from core.choices import EcoCategory
from core.utils import unique_slugify
from core.validators import UploadToUUID, image_validators


class EcoActionType(models.Model):
    """Catalogue entry configured by an administrator (fixed points, CO₂ factor)."""

    name = models.CharField('nom', max_length=120, unique=True)
    slug = models.SlugField('identifiant URL', max_length=130, unique=True, editable=False)
    description = models.TextField('description', max_length=1000)
    category = models.CharField('catégorie', max_length=20, choices=EcoCategory.choices)
    points = models.PositiveIntegerField(
        'points attribués', validators=[MinValueValidator(1), MaxValueValidator(500)],
        help_text='Valeur fixe accordée lorsqu’une déclaration est validée.',
    )
    unit = models.CharField(
        'unité de quantité', max_length=30, blank=True, help_text='Ex. : km, kg, repas, jour.'
    )
    co2_factor_kg = models.DecimalField(
        'facteur CO₂ (kg CO₂e par unité)', max_digits=8, decimal_places=3, null=True, blank=True,
        validators=[MinValueValidator(Decimal('0'))],
        help_text='Facteur configurable servant uniquement à calculer une estimation.',
    )
    factor_source = models.CharField(
        'source du facteur', max_length=255, blank=True,
        help_text='Référence documentaire du facteur (obligatoire si un facteur est renseigné).',
    )
    instructions = models.TextField('consignes de validation', max_length=1500, blank=True)
    requires_evidence = models.BooleanField('photo justificative obligatoire', default=False)
    requires_quantity = models.BooleanField('quantité obligatoire', default=False)
    is_active = models.BooleanField('active', default=True)
    created_at = models.DateTimeField('créée le', auto_now_add=True)
    updated_at = models.DateTimeField('mise à jour le', auto_now=True)

    class Meta:
        verbose_name = 'type d’action écologique'
        verbose_name_plural = 'catalogue des actions écologiques'
        ordering = ['category', 'name']
        indexes = [models.Index(fields=['is_active', 'category'])]
        constraints = [
            models.CheckConstraint(condition=models.Q(points__gte=1), name='action_type_points_positive'),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(self, self.name)
        super().save(*args, **kwargs)

    def estimate_co2(self, quantity):
        if self.co2_factor_kg is None or not quantity:
            return None
        return (Decimal(quantity) * self.co2_factor_kg).quantize(Decimal('0.001'))


class ActionSubmission(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending', 'En attente de validation'
        APPROVED = 'approved', 'Validée'
        REJECTED = 'rejected', 'Refusée'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='action_submissions', verbose_name='auteur'
    )
    action_type = models.ForeignKey(
        EcoActionType, on_delete=models.PROTECT, related_name='submissions', verbose_name='action'
    )
    challenge = models.ForeignKey(
        'challenges.Challenge', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='action_submissions', verbose_name='défi associé',
    )
    team = models.ForeignKey(
        'teams.Team', on_delete=models.SET_NULL, null=True, blank=True, related_name='action_submissions',
        verbose_name='équipe créditée',
    )
    description = models.TextField('description', max_length=1000)
    performed_on = models.DateField('date de réalisation')
    quantity = models.DecimalField(
        'quantité', max_digits=8, decimal_places=2, null=True, blank=True,
        validators=[MinValueValidator(Decimal('0.01')), MaxValueValidator(Decimal('10000'))],
    )
    evidence = models.ImageField(
        'photo justificative', upload_to=UploadToUUID('evidence'), blank=True, validators=image_validators
    )
    status = models.CharField('statut', max_length=20, choices=Status.choices, default=Status.PENDING)
    moderation_notes = models.TextField('commentaire de modération', max_length=1000, blank=True)
    points_awarded = models.PositiveIntegerField('points attribués', default=0)
    co2_saved_kg = models.DecimalField(
        'CO₂ évité estimé (kg)', max_digits=10, decimal_places=3, null=True, blank=True
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='reviewed_submissions', verbose_name='modérateur',
    )
    reviewed_at = models.DateTimeField('modérée le', null=True, blank=True)
    created_at = models.DateTimeField('déclarée le', auto_now_add=True)
    updated_at = models.DateTimeField('mise à jour le', auto_now=True)
    # Garde-fou « une seule déclaration par action et par jour », recalculé
    # dans save(). Vaut NULL pour une déclaration refusée : l'utilisateur peut
    # alors redéclarer la même action le même jour. MySQL comme PostgreSQL
    # autorisent plusieurs NULL dans un index unique, ce qui reproduit la
    # contrainte partielle d'origine sur les deux moteurs.
    dedupe_key = models.CharField(max_length=120, unique=True, null=True, editable=False)

    class Meta:
        verbose_name = 'déclaration d’action'
        verbose_name_plural = 'déclarations d’actions'
        ordering = ['-performed_on', '-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['team', 'status']),
        ]
        permissions = [('moderate_actionsubmission', 'Peut modérer les déclarations d’actions')]

    def __str__(self):
        return f'{self.action_type} — {self.user} ({self.performed_on:%d/%m/%Y})'

    def build_dedupe_key(self):
        """Clé d'unicité, ou None quand la déclaration est refusée."""
        if self.status == self.Status.REJECTED:
            return None
        if not (self.user_id and self.action_type_id and self.performed_on):
            return None
        return f'{self.user_id}:{self.action_type_id}:{self.performed_on:%Y-%m-%d}'

    def save(self, *args, **kwargs):
        self.dedupe_key = self.build_dedupe_key()
        update_fields = kwargs.get('update_fields')
        if update_fields is not None:
            kwargs['update_fields'] = {*update_fields, 'dedupe_key'}
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('actions:detail', args=[self.pk])

    @property
    def is_editable(self):
        return self.status == self.Status.PENDING

    @property
    def co2_estimate(self):
        if self.co2_saved_kg is not None:
            return self.co2_saved_kg
        return self.action_type.estimate_co2(self.quantity)


class ModerationLog(models.Model):
    """History of every moderation decision taken on a submission."""

    class Decision(models.TextChoices):
        APPROVED = 'approved', 'Validation'
        REJECTED = 'rejected', 'Refus'
        REVOKED = 'revoked', 'Annulation d’une validation'

    submission = models.ForeignKey(
        ActionSubmission, on_delete=models.CASCADE, related_name='moderation_logs', verbose_name='déclaration'
    )
    moderator = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='+', verbose_name='modérateur'
    )
    decision = models.CharField('décision', max_length=20, choices=Decision.choices)
    previous_status = models.CharField('statut précédent', max_length=20)
    new_status = models.CharField('nouveau statut', max_length=20)
    notes = models.TextField('motif', max_length=1000, blank=True)
    points_delta = models.IntegerField('variation de points', default=0)
    created_at = models.DateTimeField('date', default=timezone.now)

    class Meta:
        verbose_name = 'décision de modération'
        verbose_name_plural = 'historique de modération'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.get_decision_display()} — {self.submission}'
