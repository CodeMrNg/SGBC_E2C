from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0010_departement_code_slug'),
    ]

    operations = [
        migrations.AlterField(
            model_name='departement',
            name='code',
            field=models.CharField(max_length=50, unique=True),
        ),
        migrations.AlterField(
            model_name='departement',
            name='slug',
            field=models.SlugField(max_length=160, unique=True),
        ),
    ]
