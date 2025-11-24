import uuid

from django.conf import settings
from django.db import models


class StatutArchivage(models.TextChoices):
    ACTIF = ('actif', 'Actif')
    ARCHIVE = ('archive', 'Archive')


class Document(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type_document = models.CharField(max_length=50)
    reference_fonctionnelle = models.CharField(max_length=255)
    chemin_fichier = models.CharField(max_length=500)
    hash_contenu = models.CharField(max_length=128, blank=True)
    id_utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='documents',
    )
    date_generation = models.DateTimeField(auto_now_add=True)
    statut_archivage = models.CharField(
        max_length=20,
        choices=StatutArchivage.choices,
        default=StatutArchivage.ACTIF,
    )

    def __str__(self) -> str:
        return f'{self.type_document} - {self.reference_fonctionnelle}'


class SignatureNumerique(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id_document = models.ForeignKey(
        'Document',
        on_delete=models.CASCADE,
        related_name='signatures',
    )
    id_utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='signatures',
    )
    certificat = models.TextField()
    empreinte = models.CharField(max_length=128)
    date_signature = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f'Signature {self.id_signature} - {self.id_document}'
