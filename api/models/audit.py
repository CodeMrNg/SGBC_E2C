import uuid

from django.conf import settings
from django.db import models


class HistoriqueStatut(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    type_objet = models.CharField(max_length=50)
    id_objet = models.UUIDField(null=True, blank=True)
    ancien_statut = models.CharField(max_length=50, blank=True)
    nouveau_statut = models.CharField(max_length=50, blank=True)
    date_modification = models.DateTimeField(auto_now_add=True)
    id_utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='historique_statuts',
        null=True,
        blank=True,
    )
    commentaire = models.TextField(blank=True)

    def __str__(self) -> str:
        return f'{self.type_objet} - {self.id_objet}'


class AuditLog(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id_utilisateur = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='audit_logs',
        null=True,
        blank=True,
    )
    action = models.CharField(max_length=50)
    type_objet = models.CharField(max_length=50)
    id_objet = models.UUIDField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_client = models.GenericIPAddressField(null=True, blank=True)
    details = models.TextField(blank=True)

    def __str__(self) -> str:
        return f'{self.action} - {self.type_objet}'
