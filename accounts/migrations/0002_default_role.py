from django.conf import settings
from django.db import migrations


def create_default_role(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Role = apps.get_model('accounts', 'Role')
    group, _ = Group.objects.get_or_create(name=settings.ECOTEAMS_DEFAULT_ROLE)
    Role.objects.get_or_create(
        group=group,
        defaults={'description': 'Rôle attribué automatiquement à chaque nouvel inscrit.', 'is_system': True},
    )


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0001_initial'),
        ('auth', '0012_alter_user_first_name_max_length'),
    ]

    operations = [migrations.RunPython(create_default_role, migrations.RunPython.noop)]
