from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.db.models import Q

from .models import Role, User


def users_with_perm(perm):
    """Active users holding ``perm`` ('app_label.codename'), superusers included."""
    app_label, codename = perm.split('.')
    permission = Permission.objects.filter(content_type__app_label=app_label, codename=codename).first()
    condition = Q(is_superuser=True)
    if permission is not None:
        condition |= Q(groups__permissions=permission) | Q(user_permissions=permission)
    return User.objects.filter(condition, is_active=True).distinct()


def get_default_role_group():
    group, _ = Group.objects.get_or_create(name=settings.ECOTEAMS_DEFAULT_ROLE)
    Role.objects.get_or_create(
        group=group,
        defaults={'description': 'Rôle attribué automatiquement à chaque nouvel inscrit.', 'is_system': True},
    )
    return group


def assign_default_role(user):
    user.groups.add(get_default_role_group())
