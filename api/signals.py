from django.db.models.signals import post_save
from django.dispatch import receiver

from .models.transferts import Transfert


@receiver(post_save, sender=Transfert)
def retain_demande_access_on_transfer(sender, instance, created, **kwargs):
    if not created:
        return
    demande = instance.id_demande
    agent = instance.agent
    if demande and agent:
        demande.utilisateurs_transferts.add(agent)
