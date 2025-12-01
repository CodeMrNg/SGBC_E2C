from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0005_demande_documents_and_statut'),
    ]

    operations = [
        migrations.AddField(
            model_name='boncommande',
            name='documents',
            field=models.ManyToManyField(blank=True, related_name='bons_commande', to='api.document'),
        ),
    ]
