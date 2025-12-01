import re

from django.db import migrations
from django.utils.text import slugify


def _sigle_from_nom(nom: str) -> str:
    words = re.findall(r'[A-Za-zÀ-ÖØ-öø-ÿ]+', nom or '')
    if words:
        sigle = ''.join(w[0] for w in words if w).upper()
        if sigle:
            return sigle[:6]
    base = slugify(nom).upper().replace('-', '') or 'DEP'
    return base[:6]


def _next_seq(base: str, existing_codes):
    max_seq = 0
    for code in existing_codes:
        m = re.match(rf'^{re.escape(base)}-(\d+)$', code or '')
        if m:
            max_seq = max(max_seq, int(m.group(1)))
    return max_seq + 1


def _forward(apps, schema_editor):
    Departement = apps.get_model('api', 'Departement')
    existing = set(Departement.objects.values_list('code', flat=True))
    for dep in Departement.objects.all():
        base = _sigle_from_nom(dep.nom)
        seq = _next_seq(base, existing)
        new_code = base if seq == 1 else f'{base}-{seq:02d}'
        if dep.code != new_code:
            dep.code = new_code
            dep.save(update_fields=['code'])
            existing.add(new_code)


def _backward(apps, schema_editor):
    # Pas de retour fiable vers les anciens codes : on laisse en l'état.
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0011_alter_departement_unique'),
    ]

    operations = [
        migrations.RunPython(_forward, _backward),
    ]
