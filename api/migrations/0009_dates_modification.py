from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0008_update_statuts'),
    ]

    operations = [
        migrations.AddField(
            model_name='demande',
            name='date_modification',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AddField(
            model_name='boncommande',
            name='date_modification',
            field=models.DateTimeField(auto_now=True),
        ),
    ]
