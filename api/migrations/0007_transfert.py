from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0006_boncommande_documents'),
    ]

    operations = [
        migrations.CreateModel(
            name='Transfert',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('statut', models.CharField(choices=[('valide', 'Valide'), ('rejete', 'Rejete')], default='valide', max_length=20)),
                ('raison', models.TextField(blank=True)),
                ('date_transfert', models.DateTimeField(auto_now_add=True)),
                ('agent', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='transferts_effectues', to='api.utilisateur')),
                ('departement_beneficiaire', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='transferts_entrants', to='api.departement')),
                ('departement_source', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='transferts_sortants', to='api.departement')),
                ('id_bc', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='transferts', to='api.boncommande')),
                ('id_demande', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='transferts', to='api.demande')),
            ],
        ),
    ]
