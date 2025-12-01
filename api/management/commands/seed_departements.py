import json

from django.core.management.base import BaseCommand

from api.models import Departement


DATA = {
    "directions": [
        {
            "nom": "Direction Générale",
            "slug": "direction-generale",
            "code": "DG",
            "description": "Supervision globale et pilotage stratégique",
            "actif": True,
        },
        {
            "nom": "Direction Générale Adjointe",
            "slug": "direction-generale-adjointe",
            "code": "DGA",
            "description": "Appui direct au Directeur Général",
            "actif": True,
        },
        {
            "nom": "Direction de la Production et du Transport",
            "slug": "direction-production-transport",
            "code": "DPT",
            "description": "Supervision de la production et du transport",
            "actif": True,
        },
        {
            "nom": "Direction de la Distribution",
            "slug": "direction-distribution",
            "code": "DDI",
            "description": "Gestion et optimisation de la distribution",
            "actif": True,
        },
        {
            "nom": "Direction Commerciale",
            "slug": "direction-commerciale",
            "code": "DC",
            "description": "Stratégie commerciale et développement des ventes",
            "actif": True,
        },
        {
            "nom": "Direction Financière et Comptable",
            "slug": "direction-financiere-comptable",
            "code": "DFC",
            "description": "Gestion financière, comptable et budgétaire",
            "actif": True,
        },
        {
            "nom": "Direction de l’Administration et des Ressources Humaines",
            "slug": "direction-administration-rh",
            "code": "DARH",
            "description": "Gestion administrative et ressources humaines",
            "actif": True,
        },
        {
            "nom": "Direction d’Exploitation",
            "slug": "direction-exploitation",
            "code": "DEX",
            "description": "Supervision des opérations et de l’exploitation quotidienne",
            "actif": True,
        },
    ],
    "departements": [
        {
            "nom": "Département Patrimoine, Filiales et Participations",
            "slug": "departement-patrimoine-filiales-participations",
            "code": "DPFP",
            "description": "Gestion du patrimoine, des filiales et des participations",
            "actif": True,
        },
        {
            "nom": "Département Systèmes d’Information",
            "slug": "departement-systemes-information",
            "code": "DSI",
            "description": "Gestion des systèmes d’information et infrastructure IT",
            "actif": True,
        },
        {
            "nom": "Département Programmation des Investissements et Contrôle de Gestion",
            "slug": "departement-investissements-controle-gestion",
            "code": "DPICG",
            "description": "Planification des investissements et contrôle de gestion",
            "actif": True,
        },
        {
            "nom": "Département Audit Interne",
            "slug": "departement-audit-interne",
            "code": "DAI",
            "description": "Audit interne, conformité et analyse des risques",
            "actif": True,
        },
        {
            "nom": "Département Achats et Approvisionnements",
            "slug": "departement-achats-approvisionnements",
            "code": "DAA",
            "description": "Achats, fournisseurs et gestion des approvisionnements",
            "actif": True,
        },
        {
            "nom": "Département Logistique et Moyens Généraux",
            "slug": "departement-logistique-moyens-generaux",
            "code": "DLMG",
            "description": "Logistique et gestion des moyens généraux",
            "actif": True,
        },
        {
            "nom": "Département Qualité, Hygiène, Sécurité et Environnement",
            "slug": "departement-qhse",
            "code": "DQHSE",
            "description": "Gestion QHSE et conformité réglementaire",
            "actif": True,
        },
    ],
}


class Command(BaseCommand):
    help = "Seed des directions et départements de base."

    def handle(self, *args, **options):
        created = 0
        updated = 0
        for entry in DATA["directions"] + DATA["departements"]:
            obj, was_created = Departement.objects.update_or_create(
                code=entry["code"],
                defaults={
                    "nom": entry["nom"],
                    "slug": entry["slug"],
                    "description": entry.get("description", ""),
                    "actif": entry.get("actif", True),
                },
            )
            created += 1 if was_created else 0
            updated += 0 if was_created else 1
        self.stdout.write(self.style.SUCCESS(f"Seed terminé: {created} créés, {updated} mis à jour"))
