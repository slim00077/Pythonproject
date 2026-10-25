from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

from .services import assign_default_role


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def give_default_role(sender, instance, created, raw=False, **kwargs):
    """Every new account (registration, seed, createsuperuser) gets the User role."""
    if created and not raw:
        assign_default_role(instance)
