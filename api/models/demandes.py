import uuid

from django.db import models


class StatutDemande(models.TextChoices):
    EN_ATTENTE = ('en_attente', 'En attente')
    EN_COURS = ('en_cours', 'En cours')
    VALIDER = ('valider', 'Valider')
    REJETER = ('rejecter', 'Rejecter')


class Demande(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    numero_demande = models.CharField(max_length=100, unique=True)
    objet = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    source = models.CharField(max_length=150, blank=True, default='')
    date_creation = models.DateTimeField(auto_now_add=True)
    date_validation_budget = models.DateTimeField(null=True, blank=True)
    statut_demande = models.CharField(
        max_length=20,
        choices=StatutDemande.choices,
        default=StatutDemande.EN_ATTENTE,
    )
    id_departement = models.ForeignKey(
        'Departement',
        on_delete=models.PROTECT,
        related_name='demandes',
    )

    def __str__(self) -> str:
        return self.numero_demande


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
    id_fournisseur = models.ForeignKey(
        'Fournisseur',
        on_delete=models.SET_NULL,
        related_name='lignes_proposees',
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
