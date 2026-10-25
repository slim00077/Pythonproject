from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone

from core.choices import EcoCategory
from core.utils import unique_slugify
from core.validators import UploadToUUID, image_validators

RESERVED_TEAM_SLUGS = {'create', 'mine', 'edit', 'delete'}


class Team(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'active', 'Active'
        INACTIVE = 'inactive', 'En pause'
        ARCHIVED = 'archived', 'Archivée'

    name = models.CharField('nom', max_length=80, unique=True)
    slug = models.SlugField('identifiant URL', max_length=90, unique=True, editable=False)
    description = models.TextField('description', max_length=1000)
    motto = models.CharField('devise', max_length=140, blank=True)
    logo = models.ImageField('logo', upload_to=UploadToUUID('teams'), blank=True, validators=image_validators)
    focus_area = models.CharField(
        'domaine prioritaire', max_length=20, choices=EcoCategory.choices, default=EcoCategory.RECYCLING
    )
    captain = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='captained_teams',
        verbose_name='capitaine',
    )
    organization = models.ForeignKey(
        'organizations.Organization', on_delete=models.SET_NULL, null=True, blank=True, related_name='teams',
        verbose_name='organisation (équipe de travail)',
        help_text='Une équipe rattachée à une organisation n’accepte que les membres de cette organisation.',
    )
    status = models.CharField('statut', max_length=20, choices=Status.choices, default=Status.ACTIVE)
    is_open = models.BooleanField('ouverte aux nouveaux membres', default=True)
    max_members = models.PositiveSmallIntegerField(
        'nombre maximum de membres', default=8, validators=[MinValueValidator(2), MaxValueValidator(50)]
    )
    goal_points = models.PositiveIntegerField(
        'objectif de points', null=True, blank=True, validators=[MinValueValidator(10)],
        help_text='Objectif collectif facultatif, affiché sous forme de barre de progression.',
    )
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL, through='Membership', related_name='teams', verbose_name='membres'
    )
    created_at = models.DateTimeField('créée le', auto_now_add=True)
    updated_at = models.DateTimeField('mise à jour le', auto_now=True)

    class Meta:
        verbose_name = 'équipe'
        verbose_name_plural = 'équipes'
        ordering = ['name']
        indexes = [models.Index(fields=['status', 'focus_area'])]
        constraints = [
            models.CheckConstraint(condition=models.Q(max_members__gte=2), name='team_min_two_members'),
        ]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(self, self.name, reserved=RESERVED_TEAM_SLUGS)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('teams:detail', args=[self.slug])

    @property
    def member_count(self):
        return self.memberships.count()

    @property
    def is_full(self):
        return self.member_count >= self.max_members

    @property
    def accepts_members(self):
        return self.status == self.Status.ACTIVE and self.is_open and not self.is_full


class Membership(models.Model):
    class Role(models.TextChoices):
        CAPTAIN = 'captain', 'Capitaine'
        MEMBER = 'member', 'Membre'

    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='memberships', verbose_name='équipe')
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='memberships', verbose_name='utilisateur'
    )
    role = models.CharField('rôle dans l’équipe', max_length=20, choices=Role.choices, default=Role.MEMBER)
    joined_at = models.DateTimeField('date d’adhésion', default=timezone.now)
    # Vaut l'identifiant de l'équipe pour le capitaine, NULL pour un membre
    # simple : l'index unique garantit donc « un seul capitaine par équipe ».
    # MySQL n'implémentant pas les contraintes uniques conditionnelles, cette
    # colonne remplace l'ancienne UniqueConstraint(condition=...) et donne le
    # même résultat sur MySQL comme sur PostgreSQL.
    captain_of = models.PositiveBigIntegerField(unique=True, null=True, editable=False)

    class Meta:
        verbose_name = 'adhésion'
        verbose_name_plural = 'adhésions'
        ordering = ['-role', 'joined_at']
        constraints = [
            # One team per user in this version of the competition.
            models.UniqueConstraint(fields=['user'], name='one_team_per_user'),
        ]

    def __str__(self):
        return f'{self.user} — {self.team} ({self.get_role_display()})'

    def save(self, *args, **kwargs):
        self.captain_of = self.team_id if self.role == self.Role.CAPTAIN else None
        update_fields = kwargs.get('update_fields')
        if update_fields is not None:
            kwargs['update_fields'] = {*update_fields, 'captain_of'}
        super().save(*args, **kwargs)
