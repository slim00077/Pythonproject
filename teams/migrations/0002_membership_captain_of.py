"""
Remplace la contrainte unique conditionnelle « one_captain_per_team » par une
colonne ``captain_of`` portable.

MySQL/MariaDB n'implémente pas les contraintes uniques avec condition (avis
models.W036) : l'index n'était pas créé et la règle « un seul capitaine par
équipe » n'était plus garantie en base sur ce moteur. ``captain_of`` vaut
l'identifiant de l'équipe pour le capitaine et NULL pour les autres membres,
ce qui reproduit la contrainte sur les deux moteurs.
"""

from django.db import migrations, models


def fill_captain_of(apps, schema_editor):
    Membership = apps.get_model('teams', 'Membership')
    seen = set()
    for membership in Membership.objects.filter(role='captain').order_by('pk').iterator():
        if membership.team_id in seen:
            # Équipe comptant déjà un capitaine enregistré : on laisse NULL
            # plutôt que de bloquer la migration ou de modifier les données.
            continue
        seen.add(membership.team_id)
        Membership.objects.filter(pk=membership.pk).update(captain_of=membership.team_id)


def clear_captain_of(apps, schema_editor):
    Membership = apps.get_model('teams', 'Membership')
    Membership.objects.update(captain_of=None)


class Migration(migrations.Migration):

    dependencies = [
        ('teams', '0001_initial'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='membership',
            name='one_captain_per_team',
        ),
        migrations.AddField(
            model_name='membership',
            name='captain_of',
            field=models.PositiveBigIntegerField(editable=False, null=True),
        ),
        migrations.RunPython(fill_captain_of, clear_captain_of),
        migrations.AlterField(
            model_name='membership',
            name='captain_of',
            field=models.PositiveBigIntegerField(editable=False, null=True, unique=True),
        ),
    ]
