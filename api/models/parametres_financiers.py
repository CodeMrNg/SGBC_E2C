import uuid

from django.db import models


class Devise(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code_iso = models.CharField(max_length=10, unique=True)
    libelle = models.CharField(max_length=100)
    symbole = models.CharField(max_length=10)
    taux_reference = models.DecimalField(
        max_digits=18,
        decimal_places=6,
        null=True,
        blank=True,
    )
    actif = models.BooleanField(default=True)
    date_derniere_maj = models.DateField(null=True, blank=True)

    def __str__(self) -> str:
        return self.code_iso


class MethodePaiement(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=20, unique=True)
    libelle = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    actif = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.libelle
