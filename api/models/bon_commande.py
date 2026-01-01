import re
import uuid
from datetime import datetime

from django.conf import settings
from django.db import models, transaction


class StatutBC(models.TextChoices):
    EN_ATTENTE = ('en_attente', 'En attente')
    EN_TRAITEMENT = ('en_traitement', 'En traitement')
    VALIDER = ('valider', 'Valider')


class DecisionSignature(models.TextChoices):
    EN_ATTENTE = ('en_attente', 'En attente')
    APPROUVE = ('approuve', 'Approuve')
    REFUSE = ('refuse', 'Refuse')

class BonCommandeSequence(models.Model):
    year = models.PositiveIntegerField(primary_key=True)
    last_sequence = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Séquence bon de commande'
        verbose_name_plural = 'Séquences bons de commande'


class BonCommande(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    numero_bc = models.CharField(max_length=100, unique=True, blank=True)
    id_demande = models.ForeignKey(
        'Demande',
        on_delete=models.PROTECT,
        related_name='bons_commande',
    )
    id_fournisseur = models.ForeignKey(
        'Fournisseur',
        on_delete=models.PROTECT,
        related_name='bons_commande',
    )
    id_departement = models.ForeignKey(
        'Departement',
        on_delete=models.PROTECT,
        related_name='bons_commande',
    )
    agent_traitant = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='bons_commande_traitees',
        null=True,
        blank=True,
    )
    id_demande_valider = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='validations_bc',
        null=True,
        blank=True,
    )
    tva = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )
    remise = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )
    ca = models.CharField(max_length=50, blank=True)
    id_methode_paiement = models.ForeignKey(
        'MethodePaiement',
        on_delete=models.PROTECT,
        related_name='bons_commande',
        null=True,
        blank=True,
    )
    id_devise = models.ForeignKey(
        'Devise',
        on_delete=models.PROTECT,
        related_name='bons_commande',
    )
    montant_engage = models.DecimalField(
        max_digits=18,
        decimal_places=5,
        default=0,
    )
    id_ligne_budgetaire = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        db_column='id_ligne_budgetaire_id',
    )
    type_achat = models.CharField(max_length=100, blank=True)
    date_bc = models.DateField(null=True, blank=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    transit = models.BooleanField(default=False)
    echeance = models.DateField(null=True, blank=True)
    date_envoi_fournisseur = models.DateField(null=True, blank=True)
    conditions_paiement = models.TextField(blank=True)
    delai_livraison = models.CharField(max_length=100, blank=True)
    lieu_livraison = models.CharField(max_length=150, blank=True,null=True)
    statut_bc = models.CharField(
        max_length=20,
        choices=StatutBC.choices,
        default=StatutBC.EN_ATTENTE,
    )
    id_redacteur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='bons_commande_rediges',
    )
    documents = models.ManyToManyField(
        'Document',
        related_name='bons_commande',
        blank=True,
    )

    def __str__(self) -> str:
        return self.numero_bc

    @staticmethod
    def _next_sequence_for_year(year: int) -> int:
        """
        Retourne le prochain numéro séquentiel pour l'année donnée en se basant
        sur la première partie de numero_bc (ex: 82/DAA/DG/2025 -> 82).
        """
        existing = BonCommande.objects.filter(numero_bc__endswith=f'/{year}').values_list('numero_bc', flat=True)
        max_seq = 0
        for numero in existing:
            match = re.match(r'^(\\d+)', numero or '')
            if match:
                max_seq = max(max_seq, int(match.group(1)))
        return max_seq + 1

    @classmethod
    def generate_numero_bc(cls) -> str:
        year = datetime.now().year
        with transaction.atomic():
            sequence_obj, _ = BonCommandeSequence.objects.select_for_update().get_or_create(
                year=year,
                defaults={'last_sequence': 0},
            )
            next_sequence = sequence_obj.last_sequence + 1
            sequence_obj.last_sequence = next_sequence
            sequence_obj.save(update_fields=['last_sequence'])
        return f'BC/NUM{next_sequence}/DAA/DG/{year}'

    def save(self, *args, **kwargs):
        if not self.numero_bc:
            self.numero_bc = self.generate_numero_bc()
        super().save(*args, **kwargs)


class LigneBC(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id_bc = models.ForeignKey(
        'BonCommande',
        on_delete=models.CASCADE,
        related_name='lignes',
    )
    id_article = models.ForeignKey(
        'Article',
        on_delete=models.SET_NULL,
        related_name='lignes_bc',
        null=True,
        blank=True,
    )
    designation = models.CharField(max_length=255)
    quantite = models.DecimalField(max_digits=12, decimal_places=2)
    prix_unitaire = models.DecimalField(max_digits=18, decimal_places=2)
    id_devise = models.ForeignKey(
        'Devise',
        on_delete=models.PROTECT,
        related_name='lignes_bc',
        null=True,
        blank=True,
    )
    taux_tva = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )
    remise = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
    )
    ca = models.CharField(max_length=50, blank=True)
    prix_net = models.FloatField(
        null=True,
        blank=True,
    )

    def __str__(self) -> str:
        return f'Ligne BC {self.id} - {self.id_bc}'


class SignatureBC(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id_bc = models.ForeignKey(
        'BonCommande',
        on_delete=models.CASCADE,
        related_name='signatures',
    )
    id_signataire = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='signatures_bc',
    )
    niveau_validation = models.CharField(max_length=50)
    decision = models.CharField(
        max_length=20,
        choices=DecisionSignature.choices,
        default=DecisionSignature.EN_ATTENTE,
    )
    commentaire = models.TextField(blank=True)
    date_signature = models.DateTimeField(auto_now_add=True)
    id_document_preuve = models.ForeignKey(
        'Document',
        on_delete=models.SET_NULL,
        related_name='signatures_bc',
        null=True,
        blank=True,
    )

    def __str__(self) -> str:
        return f'Signature BC {self.id}'
