from django.db import models
from django.urls import reverse

from core.choices import EcoCategory
from core.utils import unique_slugify
from core.validators import UploadToUUID, image_validators

RESERVED_ORGANIZATION_SLUGS = {'create', 'settings', 'admin'}


class Organization(models.Model):
    """A company or an association that groups several accounts.

    Accounts join an organization through ``User.affiliation``; only users
    flagged ``is_org_manager`` can edit it. Both values are set by an
    administrator (or by the association founder at creation time) — never
    through the public sign-up form.
    """

    class Kind(models.TextChoices):
        COMPANY = 'company', 'Entreprise'
        ASSOCIATION = 'association', 'Association'
        SCHOOL = 'school', 'Établissement scolaire'

    name = models.CharField('nom', max_length=120, unique=True)
    slug = models.SlugField('identifiant URL', max_length=140, unique=True, editable=False)
    kind = models.CharField('type', max_length=20, choices=Kind.choices, default=Kind.ASSOCIATION)
    mission = models.TextField('mission', max_length=1500, blank=True)
    focus_area = models.CharField('thème environnemental principal', max_length=20, choices=EcoCategory.choices, blank=True)
    city = models.CharField('ville', max_length=80, blank=True)
    website = models.URLField('site web', blank=True)
    contact_email = models.EmailField('e-mail de contact', blank=True)
    logo = models.ImageField('logo', upload_to=UploadToUUID('organizations'), blank=True, validators=image_validators)
    is_active = models.BooleanField('active', default=True)
    created_at = models.DateTimeField('créée le', auto_now_add=True)
    updated_at = models.DateTimeField('mise à jour le', auto_now=True)

    class Meta:
        verbose_name = 'organisation'
        verbose_name_plural = 'organisations'
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = unique_slugify(self, self.name, reserved=RESERVED_ORGANIZATION_SLUGS)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('organizations:detail')
