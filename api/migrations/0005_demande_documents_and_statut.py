from django.db import migrations, models


def _forward_update_statut(apps, schema_editor):
    Demande = apps.get_model('api', 'Demande')
    Demande.objects.filter(statut_demande='en_cours').update(statut_demande='en_traitement')
    Demande.objects.filter(statut_demande='rejecter').update(statut_demande='rejeter')


def _backward_update_statut(apps, schema_editor):
    Demande = apps.get_model('api', 'Demande')
    Demande.objects.filter(statut_demande='en_traitement').update(statut_demande='en_cours')
    Demande.objects.filter(statut_demande='rejeter').update(statut_demande='rejecter')


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_demande_source'),
    ]

    operations = [
        migrations.AddField(
            model_name='demande',
            name='documents',
            field=models.ManyToManyField(blank=True, related_name='demandes', to='api.document'),
        ),
        migrations.RunPython(_forward_update_statut, _backward_update_statut),
        migrations.AlterField(
            model_name='demande',
            name='statut_demande',
            field=models.CharField(
                choices=[
                    ('en_attente', 'En attente'),
                    ('en_traitement', 'En traitement'),
                    ('valider', 'Valider'),
                    ('rejeter', 'Rejeter'),
                ],
                default='en_attente',
                max_length=20,
            ),
        ),
    ]
