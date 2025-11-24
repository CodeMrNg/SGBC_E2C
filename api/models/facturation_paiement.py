import uuid

from django.conf import settings
from django.db import models


class StatutFacture(models.TextChoices):
    RECUE = ('recue', 'Recue')
    VALIDEE = ('validee', 'Validee')
    ATTENTE_PAIEMENT = ('attente_paiement', 'En attente de paiement')
    PAYEE = ('payee', 'Payee')
    REJETEE = ('rejetee', 'Rejetee')


class StatutPaiement(models.TextChoices):
    EN_ATTENTE = ('en_attente', 'En attente')
    EN_COURS = ('en_cours', 'En cours')
    EXECUTE = ('execute', 'Execute')
    REJETE = ('rejete', 'Rejete')


class Facture(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id_bc = models.ForeignKey(
        'BonCommande',
        on_delete=models.PROTECT,
        related_name='factures',
    )
    numero_facture = models.CharField(max_length=100)
    id_devise = models.ForeignKey(
        'Devise',
        on_delete=models.PROTECT,
        related_name='factures',
    )
    montant_ht = models.DecimalField(max_digits=18, decimal_places=2)
    montant_ttc = models.DecimalField(max_digits=18, decimal_places=2)
    date_facture = models.DateField()
    date_reception = models.DateField(null=True, blank=True)
    statut_facture = models.CharField(
        max_length=20,
        choices=StatutFacture.choices,
        default=StatutFacture.RECUE,
    )
    id_document_facture = models.ForeignKey(
        'Document',
        on_delete=models.SET_NULL,
        related_name='factures',
        null=True,
        blank=True,
    )
    id_agent_comptable = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='factures_traitees',
        null=True,
        blank=True,
    )

    def __str__(self) -> str:
        return f'Facture {self.numero_facture}'


class Paiement(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id_facture = models.ForeignKey(
        'Facture',
        on_delete=models.PROTECT,
        related_name='paiements',
    )
    id_banque = models.ForeignKey(
        'Banque',
        on_delete=models.PROTECT,
        related_name='paiements',
    )
    id_methode_paiement = models.ForeignKey(
        'MethodePaiement',
        on_delete=models.PROTECT,
        related_name='paiements',
    )
    montant = models.DecimalField(max_digits=18, decimal_places=2)
    date_ordre = models.DateField(null=True, blank=True)
    date_execution = models.DateField(null=True, blank=True)
    reference_virement = models.CharField(max_length=150, blank=True)
    statut_paiement = models.CharField(
        max_length=20,
        choices=StatutPaiement.choices,
        default=StatutPaiement.EN_ATTENTE,
    )
    id_preuve_paiement = models.ForeignKey(
        'Document',
        on_delete=models.SET_NULL,
        related_name='paiements',
        null=True,
        blank=True,
    )
    id_tresorier = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='paiements_valides',
        null=True,
        blank=True,
    )

    def __str__(self) -> str:
        return f'Paiement {self.id}'
