"""
Remplace la contrainte unique conditionnelle « unique_daily_action_submission »
par une colonne ``dedupe_key`` portable.

MySQL/MariaDB n'implémente pas les contraintes uniques avec condition : Django
émettait l'avertissement models.W036 et l'index n'était tout simplement pas
créé, ce qui faisait disparaître la protection anti-doublon sur ce moteur. La
colonne ``dedupe_key`` (NULL pour les déclarations refusées) reproduit le même
effet sur MySQL comme sur PostgreSQL.
"""

from django.db import migrations, models


def fill_dedupe_key(apps, schema_editor):
    ActionSubmission = apps.get_model('actions', 'ActionSubmission')
    seen = set()
    for submission in ActionSubmission.objects.order_by('pk').iterator():
        if submission.status == 'rejected':
            continue
        key = f'{submission.user_id}:{submission.action_type_id}:{submission.performed_on:%Y-%m-%d}'
        if key in seen:
            # Doublon déjà présent en base (créé avant cette migration) : on
            # laisse la clé à NULL pour ne pas bloquer la migration et ne pas
            # supprimer de données existantes.
            continue
        seen.add(key)
        ActionSubmission.objects.filter(pk=submission.pk).update(dedupe_key=key)


def clear_dedupe_key(apps, schema_editor):
    ActionSubmission = apps.get_model('actions', 'ActionSubmission')
    ActionSubmission.objects.update(dedupe_key=None)


class Migration(migrations.Migration):

    dependencies = [
        ('actions', '0001_initial'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='actionsubmission',
            name='unique_daily_action_submission',
        ),
        migrations.AddField(
            model_name='actionsubmission',
            name='dedupe_key',
            field=models.CharField(editable=False, max_length=120, null=True),
        ),
        migrations.RunPython(fill_dedupe_key, clear_dedupe_key),
        migrations.AlterField(
            model_name='actionsubmission',
            name='dedupe_key',
            field=models.CharField(editable=False, max_length=120, null=True, unique=True),
        ),
    ]
