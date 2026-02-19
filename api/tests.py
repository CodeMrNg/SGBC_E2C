from django.db import models
from django.test import TestCase

from .models import Demande, Departement, Transfert, Utilisateur
from .serializers.resources import DemandeSerializer


class DemandeSourceSerializerTests(TestCase):
    def setUp(self):
        self.departement_source = Departement.objects.create(nom='Direction Source')
        self.departement_beneficiaire = Departement.objects.create(nom='Direction Beneficiaire')
        self.departement_final = Departement.objects.create(nom='Direction Finale')
        self.agent = Utilisateur.objects.create_user(
            login='agent-transfer',
            email='agent-transfer@example.com',
            phone='+243900000001',
            password='secret123',
            first_name='Agent',
            last_name='Transfer',
        )

    def test_source_returns_initiating_department_without_transfer(self):
        demande = Demande.objects.create(
            objet='Achat de materiel',
            id_departement=self.departement_source,
            source='Interne',
        )

        data = DemandeSerializer(demande).data

        self.assertEqual(data['source'], self.departement_source.nom)

    def test_source_keeps_first_department_after_transfers(self):
        demande = Demande.objects.create(
            objet='Achat de materiel',
            id_departement=self.departement_source,
            source='Interne',
        )

        demande.id_departement = self.departement_beneficiaire
        demande.save(update_fields=['id_departement'])
        Transfert.objects.create(
            departement_source=self.departement_source,
            departement_beneficiaire=self.departement_beneficiaire,
            agent=self.agent,
            id_demande=demande,
            raison='Traitement par le departement beneficiaire',
        )

        demande.id_departement = self.departement_final
        demande.save(update_fields=['id_departement'])
        Transfert.objects.create(
            departement_source=self.departement_beneficiaire,
            departement_beneficiaire=self.departement_final,
            agent=self.agent,
            id_demande=demande,
            raison='Traitement final',
        )

        demande_prefetchee = Demande.objects.prefetch_related(
            models.Prefetch(
                'transferts',
                queryset=Transfert.objects.select_related('departement_source'),
            )
        ).get(pk=demande.pk)

        data = DemandeSerializer(demande_prefetchee).data

        self.assertEqual(data['source'], self.departement_source.nom)

    def test_create_sets_source_to_department_name(self):
        serializer = DemandeSerializer(
            data={
                'objet': 'Nouvelle demande',
                'id_departement': str(self.departement_source.id),
            }
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        demande = serializer.save()

        self.assertEqual(demande.source, self.departement_source.nom)
