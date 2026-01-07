import re
import uuid
from datetime import datetime

from django.conf import settings
from django.db import models


class StatutDemande(models.TextChoices):
    BROUILLON = ('brouillon', 'Brouillon')
    EN_ATTENTE = ('en_attente', 'En attente')
    EN_TRAITEMENT = ('en_traitement', 'En traitement')
    VALIDER = ('valider', 'Valider')
    REJETER = ('rejeter', 'Rejeter')


class DecisionDemande(models.TextChoices):
    EN_ATTENTE = ('en_attente', 'En attente')
    APPROUVE = ('approuve', 'Approuve')
    REFUSE = ('refuse', 'Refuse')


class Demande(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    numero_demande = models.CharField(max_length=100, unique=True)
    objet = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    source = models.CharField(max_length=150, blank=True, default='')
    canal = models.CharField(max_length=150, blank=True, default='')
    rapport_daa = models.TextField(blank=True, null=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    date_validation_budget = models.DateTimeField(null=True, blank=True)
    statut_demande = models.CharField(
        max_length=20,
        choices=StatutDemande.choices,
        default=StatutDemande.EN_ATTENTE,
    )
    decision = models.CharField(
        max_length=20,
        choices=DecisionDemande.choices,
        default=DecisionDemande.EN_ATTENTE,
    )
    commentaire = models.TextField(blank=True)
    date_signature = models.DateTimeField(null=True, blank=True)
    id_departement = models.ForeignKey(
        'Departement',
        on_delete=models.PROTECT,
        related_name='demandes',
    )
    id_fournisseur = models.ForeignKey(
        'Fournisseur',
        on_delete=models.SET_NULL,
        related_name='demandes',
        null=True,
        blank=True,
    )
    agent_traitant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='demandes_traitees',
        null=True,
        blank=True,
    )
    id_signataire = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='demandes_signees',
        null=True,
        blank=True,
    )
    id_document_preuve = models.ForeignKey(
        'Document',
        on_delete=models.SET_NULL,
        related_name='demandes_signature',
        null=True,
        blank=True,
    )
    documents = models.ManyToManyField(
        'Document',
        related_name='demandes',
        blank=True,
    )
    utilisateurs_transferts = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='demandes_transferees',
        blank=True,
    )

    def __str__(self) -> str:
        return self.numero_demande

    @staticmethod
    def _next_sequence_for_year(year: int) -> int:
        """
        Retourne le prochain numéro séquentiel pour l'année donnée.
        Cherche les numéros existants au format DM/NUMXX/{year}/ pour continuer la séquence.
        """
        existing = Demande.objects.filter(numero_demande__endswith=f'/{year}/').values_list(
            'numero_demande', flat=True
        )
        max_seq = 0
        for numero in existing:
            match = re.search(rf'DM/NUM(\d+)/{year}/', numero or '')
            if match:
                max_seq = max(max_seq, int(match.group(1)))
        return max_seq + 1

    @classmethod
    def generate_numero_demande(cls) -> str:
        year = datetime.now().year
        sequence = cls._next_sequence_for_year(year)
        return f'DM/NUM{sequence:02d}/{year}/'

    def save(self, *args, **kwargs):
        if not self.numero_demande:
            self.numero_demande = self.generate_numero_demande()
        super().save(*args, **kwargs)

# on selectionne le type qui peut etre soit 'Article' soit 'Service'  puis une designation 
class LigneDemande(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id_demande = models.ForeignKey(
        'Demande',
        on_delete=models.CASCADE,
        related_name='lignes',
    )
    id_article = models.ForeignKey(
        'Article',
        on_delete=models.SET_NULL,
        related_name='lignes_demande',
        null=True,
        blank=True,
    )
    designation = models.CharField(max_length=255)
    quantite = models.DecimalField(max_digits=12, decimal_places=2)
    prix_unitaire_estime = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        null=True,
        blank=True,
    )
    id_devise = models.ForeignKey(
        'Devise',
        on_delete=models.PROTECT,
        related_name='lignes_demande',
        null=True,
        blank=True,
    )
    commentaire = models.TextField(blank=True)

    def __str__(self) -> str:
        return f'Ligne {self.id} de {self.id_demande}'
