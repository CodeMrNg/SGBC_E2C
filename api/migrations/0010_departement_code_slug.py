import re

from django.db import migrations, models
from django.utils.text import slugify


def _generate_code(nom, existing_codes):
    base = slugify(nom).upper().replace('-', '') or 'DEPT'
    max_seq = 0
    for code in existing_codes:
        m = re.match(rf'^{re.escape(base)}-(\d+)$', code)
        if m:
            max_seq = max(max_seq, int(m.group(1)))
    return f'{base}-{max_seq + 1:03d}'


def _forward(apps, schema_editor):
    Departement = apps.get_model('api', 'Departement')
    codes = set(Departement.objects.values_list('code', flat=True))
    for dep in Departement.objects.all():
        changed = False
        if not dep.code:
            new_code = _generate_code(dep.nom, codes)
            dep.code = new_code
            codes.add(new_code)
            changed = True
        if not dep.slug:
            base = slugify(dep.nom) or 'departement'
            slug_candidate = base
            idx = 1
            while Departement.objects.filter(slug=slug_candidate).exclude(pk=dep.pk).exists():
                idx += 1
                slug_candidate = f'{base}-{idx}'
            dep.slug = slug_candidate
            changed = True
        if changed:
            dep.save(update_fields=['code', 'slug'])


def _backward(apps, schema_editor):
    Departement = apps.get_model('api', 'Departement')
    Departement.objects.update(code='', slug='')


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0009_dates_modification'),
    ]

    operations = [
        migrations.AddField(
            model_name='departement',
            name='code',
            field=models.CharField(blank=True, max_length=50, unique=True),
        ),
        migrations.AddField(
            model_name='departement',
            name='slug',
            field=models.SlugField(blank=True, max_length=160, unique=True),
        ),
        migrations.RunPython(_forward, _backward),
    ]
