import uuid

from django.conf import settings
from django.db import models


class StatutTransfert(models.TextChoices):
    VALIDE = ('valide', 'Valide')
    REJETE = ('rejete', 'Rejete')


class Transfert(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    departement_source = models.ForeignKey(
        'Departement',
        on_delete=models.PROTECT,
        related_name='transferts_sortants',
    )
    departement_beneficiaire = models.ForeignKey(
        'Departement',
        on_delete=models.PROTECT,
        related_name='transferts_entrants',
    )
    statut = models.CharField(
        max_length=20,
        choices=StatutTransfert.choices,
        default=StatutTransfert.VALIDE,
    )
    raison = models.TextField(blank=True, null=True)
    agent = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='transferts_effectues',
    )
    id_demande = models.ForeignKey(
        'Demande',
        on_delete=models.SET_NULL,
        related_name='transferts',
        null=True,
        blank=True,
    )
    id_bc = models.ForeignKey(
        'BonCommande',
        on_delete=models.SET_NULL,
        related_name='transferts',
        null=True,
        blank=True,
    )
    date_transfert = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        cible = self.id_demande or self.id_bc
        return f'Transfert {cible or self.id} vers {self.departement_beneficiaire}'
