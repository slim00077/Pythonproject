from django.contrib.auth.models import AbstractUser, Group
from django.db import models

from core.choices import EcoCategory
from core.validators import UploadToUUID, image_validators


class User(AbstractUser):
    class OrganizationType(models.TextChoices):
        STUDENT = 'student', 'Étudiant·e / jeune'
        EMPLOYEE = 'employee', 'Salarié·e / entreprise'
        ASSOCIATION = 'association', 'Membre d’une association'
        OTHER = 'other', 'Autre'

    email = models.EmailField('adresse e-mail', unique=True)
    organization_type = models.CharField(
        'profil', max_length=20, choices=OrganizationType.choices, default=OrganizationType.STUDENT
    )
    organization = models.CharField('établissement / organisation', max_length=120, blank=True)
    city = models.CharField('ville', max_length=80, blank=True)
    bio = models.TextField('présentation', max_length=500, blank=True)
    favorite_category = models.CharField(
        'thème écologique préféré', max_length=20, choices=EcoCategory.choices, blank=True
    )
    skills = models.CharField(
        'compétences', max_length=200, blank=True,
        help_text='Ex. : communication, bricolage, cuisine, organisation d’événements…',
    )
    avatar = models.ImageField(
        'photo de profil', upload_to=UploadToUUID('avatars'), blank=True, validators=image_validators
    )

    class Meta:
        verbose_name = 'utilisateur'
        verbose_name_plural = 'utilisateurs'
        ordering = ['username']

    def __str__(self):
        return self.get_full_name() or self.username

    @property
    def display_name(self):
        return self.get_full_name() or self.username

    def save(self, *args, **kwargs):
        if self.email:
            self.email = self.email.strip().lower()
        super().save(*args, **kwargs)


class Role(models.Model):
    """Extra information attached to a Django ``Group`` used as a role."""

    group = models.OneToOneField(Group, on_delete=models.CASCADE, related_name='role', verbose_name='groupe')
    description = models.TextField('description', max_length=500, blank=True)
    is_system = models.BooleanField(
        'rôle système', default=False,
        help_text='Les rôles système ne peuvent être ni renommés ni supprimés.',
    )
    created_at = models.DateTimeField('créé le', auto_now_add=True)
    updated_at = models.DateTimeField('mis à jour le', auto_now=True)

    class Meta:
        verbose_name = 'rôle'
        verbose_name_plural = 'rôles'
        ordering = ['-is_system', 'group__name']

    def __str__(self):
        return self.group.name
