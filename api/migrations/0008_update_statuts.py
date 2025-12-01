from django.db import migrations, models


def _forward_map_statut_bc(apps, schema_editor):
    BonCommande = apps.get_model('api', 'BonCommande')
    mapping = {
        'en_redaction': 'en_attente',
        'en_signature': 'en_traitement',
        'signe': 'valider',
        'envoye': 'valider',
        'receptionne': 'valider',
    }
    for old, new in mapping.items():
        BonCommande.objects.filter(statut_bc=old).update(statut_bc=new)


def _backward_map_statut_bc(apps, schema_editor):
    BonCommande = apps.get_model('api', 'BonCommande')
    mapping = {
        'en_attente': 'en_redaction',
        'en_traitement': 'en_signature',
        'valider': 'signe',
    }
    for old, new in mapping.items():
        BonCommande.objects.filter(statut_bc=old).update(statut_bc=new)


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0007_transfert'),
    ]

    operations = [
        migrations.RunPython(_forward_map_statut_bc, _backward_map_statut_bc),
        migrations.AlterField(
            model_name='demande',
            name='statut_demande',
            field=models.CharField(
                choices=[
                    ('brouillon', 'Brouillon'),
                    ('en_attente', 'En attente'),
                    ('en_traitement', 'En traitement'),
                    ('valider', 'Valider'),
                    ('rejeter', 'Rejeter'),
                ],
                default='en_attente',
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name='boncommande',
            name='statut_bc',
            field=models.CharField(
                choices=[
                    ('en_attente', 'En attente'),
                    ('en_traitement', 'En traitement'),
                    ('valider', 'Valider'),
                ],
                default='en_attente',
                max_length=20,
            ),
        ),
    ]
