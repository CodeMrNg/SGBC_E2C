import uuid
from datetime import datetime

from django.conf import settings
from django.db import models, transaction


class StatutArchivage(models.TextChoices):
    ACTIF = ('actif', 'Actif')
    ARCHIVE = ('archive', 'Archive')


class PrioriteDocument(models.IntegerChoices):
    UN = (1, '1')
    DEUX = (2, '2')
    TROIS = (3, '3')


class DocumentSequence(models.Model):
    year = models.PositiveIntegerField(primary_key=True)
    last_sequence = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Sequence document'
        verbose_name_plural = 'Sequences documents'


class Document(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type_document = models.CharField(max_length=50)
    titre = models.CharField(max_length=255, blank=True)
    code = models.PositiveIntegerField(unique=True, editable=False, null=True, blank=True)
    reference_fonctionnelle = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    chemin_fichier = models.FileField(upload_to='documents/', max_length=500, blank=True, null=True)
    hash_contenu = models.CharField(max_length=128, blank=True)
    priorite = models.PositiveSmallIntegerField(
        choices=PrioriteDocument.choices,
        default=PrioriteDocument.UN,
    )
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

    @staticmethod
    def _global_sequence_year() -> int:
        """
        Utilise une seule séquence globale (pas de remise à zéro annuelle).
        """
        return 0

    @classmethod
    def _next_sequence(cls) -> int:
        year = cls._global_sequence_year()
        with transaction.atomic():
            sequence_obj, _ = DocumentSequence.objects.select_for_update().get_or_create(
                year=year,
                defaults={'last_sequence': 0},
            )
            next_sequence = sequence_obj.last_sequence + 1
            sequence_obj.last_sequence = next_sequence
            sequence_obj.save(update_fields=['last_sequence'])
        return next_sequence

    @classmethod
    def generate_reference_fonctionnelle(cls) -> str:
        seq = cls._next_sequence()
        return f'DOC/NUM{seq:06d}'

    def save(self, *args, **kwargs):
        if not self.code:
            seq = self._next_sequence()
            self.code = seq
            if not self.reference_fonctionnelle:
                self.reference_fonctionnelle = f'DOC/NUM{seq:06d}'
        elif not self.reference_fonctionnelle:
            self.reference_fonctionnelle = self.generate_reference_fonctionnelle()
        super().save(*args, **kwargs)


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
    certificat = models.TextField(blank=True, null=True)
    empreinte = models.CharField(max_length=128, blank=True, null=True)
    date_signature = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f'Signature {self.id_signature} - {self.id_document}'
