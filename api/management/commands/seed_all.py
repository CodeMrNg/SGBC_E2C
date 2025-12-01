from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from api.models import (
    Article,
    Banque,
    BonCommande,
    Categorie,
    Demande,
    Departement,
    Devise,
    Document,
    Facture,
    Fournisseur,
    FournisseurRIB,
    LigneBC,
    LigneBudgetaire,
    LigneDemande,
    MethodePaiement,
    Paiement,
    Role,
    SignatureBC,
    Transfert,
)


DEPARTEMENTS_DATA = [
    # Directions
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
    # Départements
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
]

DEVISES_DATA = [
    {"code_iso": "XAF", "libelle": "Franc CFA", "symbole": "CFA", "taux_reference": "1"},
    {"code_iso": "USD", "libelle": "Dollar US", "symbole": "$", "taux_reference": "620"},
    {"code_iso": "EUR", "libelle": "Euro", "symbole": "€", "taux_reference": "655.957"},
]

METHODES_PAIEMENT_DATA = [
    {"code": "VIR", "libelle": "Virement"},
    {"code": "CHQ", "libelle": "Chèque"},
    {"code": "ESP", "libelle": "Espèces"},
    {"code": "CB", "libelle": "Carte bancaire"},
]

CATEGORIES_DATA = [
    {"code": "MAT", "libelle": "Matériel"},
    {"code": "SRV", "libelle": "Services"},
    {"code": "LOG", "libelle": "Logistique"},
    {"code": "CONS", "libelle": "Consommables"},
]

FOURNISSEURS_DATA = [
    {"code_fournisseur": "F001", "raison_sociale": "Fournisseur Alpha", "email": "alpha@example.com"},
    {"code_fournisseur": "F002", "raison_sociale": "Fournisseur Beta", "email": "beta@example.com"},
    {"code_fournisseur": "F003", "raison_sociale": "Fournisseur Gamma", "email": "gamma@example.com"},
    {"code_fournisseur": "F004", "raison_sociale": "Fournisseur Delta", "email": "delta@example.com"},
]

BANQUES_DATA = [
    {"code_banque": "B001", "nom": "Banque A", "code_swift": "BKAFRAB1"},
    {"code_banque": "B002", "nom": "Banque B", "code_swift": "BKBFRAB1"},
]

ROLES_DATA = [
    {"code": "ADMIN", "libelle": "Administrateur"},
    {"code": "ACH", "libelle": "Acheteur"},
    {"code": "FIN", "libelle": "Financier"},
    {"code": "DSI", "libelle": "Responsable IT"},
]


class Command(BaseCommand):
    help = "Seed de données de démonstration sur l'ensemble des modèles principaux."

    def handle(self, *args, **options):
        dep_map = self._seed_departements()
        devise_map = self._seed_devises()
        methode_map = self._seed_methodes_paiement()
        categorie_map = self._seed_categories()
        fournisseur_map = self._seed_fournisseurs()
        banque_map = self._seed_banques()
        role_map = self._seed_roles()
        user = self._seed_user(dep_map.get("DG"), role_map.get("ADMIN"))

        # Articles
        article_laptop = Article.objects.update_or_create(
            code_article="ART-001",
            defaults={
                "designation": "Ordinateur portable",
                "id_categorie": categorie_map["MAT"],
                "unite": "Unité",
                "prix_reference": Decimal("350000"),
                "id_devise": devise_map["XAF"],
                "actif": True,
            },
        )[0]
        article_moniteur = Article.objects.update_or_create(
            code_article="ART-002",
            defaults={
                "designation": "Moniteur 24 pouces",
                "id_categorie": categorie_map["MAT"],
                "unite": "Unité",
                "prix_reference": Decimal("90000"),
                "id_devise": devise_map["XAF"],
                "actif": True,
            },
        )[0]
        article_service = Article.objects.update_or_create(
            code_article="ART-003",
            defaults={
                "designation": "Maintenance IT",
                "id_categorie": categorie_map["SRV"],
                "unite": "Forfait",
                "prix_reference": Decimal("500000"),
                "id_devise": devise_map["XAF"],
                "actif": True,
            },
        )[0]

        # Ligne budgétaire
        lb = LigneBudgetaire.objects.update_or_create(
            code_ligne="LB-2025-DAA-001",
            defaults={
                "exercice": 2025,
                "chapitre": "Investissements",
                "article_budgetaire": "Informatique",
                "paragraphe": "Matériel",
                "id_departement": dep_map["DAA"],
                "id_devise": devise_map["XAF"],
                "montant_budget": Decimal("100000000"),
                "montant_engage": Decimal("0"),
                "montant_reste": Decimal("100000000"),
            },
        )[0]
        lb2 = LigneBudgetaire.objects.update_or_create(
            code_ligne="LB-2025-DSI-001",
            defaults={
                "exercice": 2025,
                "chapitre": "Exploitation",
                "article_budgetaire": "Services IT",
                "paragraphe": "Maintenance",
                "id_departement": dep_map["DSI"],
                "id_devise": devise_map["XAF"],
                "montant_budget": Decimal("80000000"),
                "montant_engage": Decimal("0"),
                "montant_reste": Decimal("80000000"),
            },
        )[0]
        lb3 = LigneBudgetaire.objects.update_or_create(
            code_ligne="LB-2025-DPT-001",
            defaults={
                "exercice": 2025,
                "chapitre": "Production",
                "article_budgetaire": "Transport",
                "paragraphe": "Maintenance",
                "id_departement": dep_map["DPT"],
                "id_devise": devise_map["XAF"],
                "montant_budget": Decimal("50000000"),
                "montant_engage": Decimal("0"),
                "montant_reste": Decimal("50000000"),
            },
        )[0]

        # Fournisseur RIB
        FournisseurRIB.objects.update_or_create(
            id_fournisseur=fournisseur_map["F001"],
            id_banque=banque_map["B001"],
            numero_compte="1234567890",
            defaults={
                "intitule_compte": "Compte principal",
                "code_banque": "B001",
                "code_agence": "001",
                "cle_rib": "97",
                "id_devise": devise_map["XAF"],
                "actif": True,
            },
        )
        FournisseurRIB.objects.update_or_create(
            id_fournisseur=fournisseur_map["F002"],
            id_banque=banque_map["B002"],
            numero_compte="9876543210",
            defaults={
                "intitule_compte": "Compte secondaire",
                "code_banque": "B002",
                "code_agence": "002",
                "cle_rib": "45",
                "id_devise": devise_map["XAF"],
                "actif": True,
            },
        )

        # Demande
        demande = Demande.objects.update_or_create(
            numero_demande="DM-001",
            defaults={
                "objet": "Achat matériel informatique",
                "description": "Renouvellement des laptops",
                "source": "Interne",
                "id_departement": dep_map["DAA"],
            },
        )[0]

        LigneDemande.objects.update_or_create(
            id_demande=demande,
            designation="Laptop 15 pouces",
            defaults={
                "id_article": article_laptop,
                "id_fournisseur": fournisseur_map["F001"],
                "quantite": Decimal("10"),
                "prix_unitaire_estime": Decimal("350000"),
                "id_devise": devise_map["XAF"],
                "commentaire": "Configuration standard",
            },
        )

        # Demande 2
        demande2 = Demande.objects.update_or_create(
            numero_demande="DM-002",
            defaults={
                "objet": "Maintenance IT annuelle",
                "description": "Contrat de maintenance serveurs",
                "source": "Interne",
                "id_departement": dep_map["DSI"],
                "statut_demande": "en_traitement",
            },
        )[0]

        LigneDemande.objects.update_or_create(
            id_demande=demande2,
            designation="Maintenance serveurs",
            defaults={
                "id_article": article_service,
                "id_fournisseur": fournisseur_map["F002"],
                "quantite": Decimal("1"),
                "prix_unitaire_estime": Decimal("500000"),
                "id_devise": devise_map["XAF"],
                "commentaire": "Contrat annuel",
            },
        )

        # Demande 3
        demande3 = Demande.objects.update_or_create(
            numero_demande="DM-003",
            defaults={
                "objet": "Maintenance flotte véhicules",
                "description": "Révision annuelle des véhicules",
                "source": "Interne",
                "id_departement": dep_map["DPT"],
                "statut_demande": "en_attente",
            },
        )[0]

        LigneDemande.objects.update_or_create(
            id_demande=demande3,
            designation="Révision 10 véhicules",
            defaults={
                "id_article": article_service,
                "id_fournisseur": fournisseur_map["F003"],
                "quantite": Decimal("10"),
                "prix_unitaire_estime": Decimal("150000"),
                "id_devise": devise_map["XAF"],
                "commentaire": "Inclut pièces et main d'œuvre",
            },
        )

        # Bon de commande 1
        bc = BonCommande.objects.update_or_create(
            numero_bc="BC-001",
            defaults={
                "id_demande": demande,
                "id_fournisseur": fournisseur_map["F001"],
                "id_departement": dep_map["DAA"],
                "id_devise": devise_map["XAF"],
                "id_methode_paiement": methode_map["VIR"],
                "id_ligne_budgetaire": lb,
                "id_redacteur": user,
                "montant_engage": Decimal("3500000"),
            },
        )[0]

        LigneBC.objects.update_or_create(
            id_bc=bc,
            designation="Laptop 15 pouces",
            defaults={
                "id_article": article_laptop,
                "quantite": Decimal("10"),
                "prix_unitaire": Decimal("350000"),
                "id_devise": devise_map["XAF"],
                "taux_tva": Decimal("19.25"),
                "prix_net": Decimal("3500000"),
            },
        )

        # Bon de commande 2
        bc2 = BonCommande.objects.update_or_create(
            numero_bc="BC-002",
            defaults={
                "id_demande": demande2,
                "id_fournisseur": fournisseur_map["F002"],
                "id_departement": dep_map["DSI"],
                "id_devise": devise_map["XAF"],
                "id_methode_paiement": methode_map["CHQ"],
                "id_ligne_budgetaire": lb2,
                "id_redacteur": user,
                "montant_engage": Decimal("500000"),
                "statut_bc": "en_traitement",
            },
        )[0]

        LigneBC.objects.update_or_create(
            id_bc=bc2,
            designation="Maintenance serveurs",
            defaults={
                "id_article": article_service,
                "quantite": Decimal("1"),
                "prix_unitaire": Decimal("500000"),
                "id_devise": devise_map["XAF"],
                "prix_net": Decimal("500000"),
            },
        )
        LigneBC.objects.update_or_create(
            id_bc=bc2,
            designation="Moniteur 24 pouces",
            defaults={
                "id_article": article_moniteur,
                "quantite": Decimal("5"),
                "prix_unitaire": Decimal("90000"),
                "id_devise": devise_map["XAF"],
                "prix_net": Decimal("450000"),
            },
        )

        # Bon de commande 3
        bc3 = BonCommande.objects.update_or_create(
            numero_bc="BC-003",
            defaults={
                "id_demande": demande3,
                "id_fournisseur": fournisseur_map["F003"],
                "id_departement": dep_map["DPT"],
                "id_devise": devise_map["XAF"],
                "id_methode_paiement": methode_map["CB"],
                "id_ligne_budgetaire": lb3,
                "id_redacteur": user,
                "montant_engage": Decimal("1500000"),
                "statut_bc": "en_attente",
            },
        )[0]

        LigneBC.objects.update_or_create(
            id_bc=bc3,
            designation="Révision véhicule utilitaire",
            defaults={
                "id_article": article_service,
                "quantite": Decimal("5"),
                "prix_unitaire": Decimal("150000"),
                "id_devise": devise_map["XAF"],
                "prix_net": Decimal("750000"),
            },
        )

        # Document
        doc = Document.objects.update_or_create(
            reference_fonctionnelle="BC-DOC-001",
            defaults={
                "type_document": "BC",
                "chemin_fichier": "docs/bc-001.pdf",
                "id_utilisateur": user,
            },
        )[0]

        Document.objects.update_or_create(
            reference_fonctionnelle="BC-DOC-002",
            defaults={
                "type_document": "BC",
                "chemin_fichier": "docs/bc-002.pdf",
                "id_utilisateur": user,
            },
        )

        # Signature BC (preuve optionnelle)
        SignatureBC.objects.update_or_create(
            id_bc=bc,
            id_signataire=user,
            niveau_validation=1,
            defaults={"decision": "approuve"},
        )
        SignatureBC.objects.update_or_create(
            id_bc=bc2,
            id_signataire=user,
            niveau_validation=1,
            defaults={"decision": "en_attente"},
        )

        # Facture
        facture = Facture.objects.update_or_create(
            id_bc=bc,
            numero_facture="FAC-001",
            defaults={
                "id_devise": devise_map["XAF"],
                "montant_ht": Decimal("3500000"),
                "montant_ttc": Decimal("3500000"),
                "date_facture": "2025-01-01",
                "id_document_facture": doc,
            },
        )[0]
        facture2 = Facture.objects.update_or_create(
            id_bc=bc2,
            numero_facture="FAC-002",
            defaults={
                "id_devise": devise_map["XAF"],
                "montant_ht": Decimal("950000"),
                "montant_ttc": Decimal("950000"),
                "date_facture": "2025-02-01",
            },
        )[0]
        facture3 = Facture.objects.update_or_create(
            id_bc=bc3,
            numero_facture="FAC-003",
            defaults={
                "id_devise": devise_map["XAF"],
                "montant_ht": Decimal("750000"),
                "montant_ttc": Decimal("750000"),
                "date_facture": "2025-03-01",
            },
        )[0]

        # Paiement
        Paiement.objects.update_or_create(
            id_facture=facture,
            id_banque=banque_map["B001"],
            id_methode_paiement=methode_map["VIR"],
            defaults={
                "montant": Decimal("3500000"),
                "reference_virement": "VIR-001",
            },
        )
        Paiement.objects.update_or_create(
            id_facture=facture2,
            id_banque=banque_map["B002"],
            id_methode_paiement=methode_map["CHQ"],
            defaults={
                "montant": Decimal("950000"),
                "reference_virement": "CHQ-002",
            },
        )
        Paiement.objects.update_or_create(
            id_facture=facture3,
            id_banque=banque_map["B001"],
            id_methode_paiement=methode_map["CB"],
            defaults={
                "montant": Decimal("750000"),
                "reference_virement": "CB-003",
            },
        )

        # Transferts
        Transfert.objects.update_or_create(
            id_demande=demande2,
            departement_source=dep_map["DSI"],
            departement_beneficiaire=dep_map["DAA"],
            defaults={
                "statut": "valide",
                "raison": "Traitement budgétaire centralisé",
                "agent": user,
            },
        )
        Transfert.objects.update_or_create(
            id_bc=bc2,
            departement_source=dep_map["DSI"],
            departement_beneficiaire=dep_map["DAA"],
            defaults={
                "statut": "valide",
                "raison": "Alignement achats",
                "agent": user,
            },
        )
        Transfert.objects.update_or_create(
            id_demande=demande3,
            departement_source=dep_map["DPT"],
            departement_beneficiaire=dep_map["DAA"],
            defaults={
                "statut": "valide",
                "raison": "Centralisation des commandes",
                "agent": user,
            },
        )

        self.stdout.write(self.style.SUCCESS("Seed complet exécuté avec succès."))

    def _seed_departements(self):
        dep_map = {}
        for entry in DEPARTEMENTS_DATA:
            obj, _ = Departement.objects.update_or_create(
                code=entry["code"],
                defaults={
                    "nom": entry["nom"],
                    "slug": entry["slug"],
                    "description": entry.get("description", ""),
                    "actif": entry.get("actif", True),
                },
            )
            dep_map[entry["code"]] = obj
        return dep_map

    def _seed_devises(self):
        dev_map = {}
        for entry in DEVISES_DATA:
            obj, _ = Devise.objects.update_or_create(
                code_iso=entry["code_iso"],
                defaults={
                    "libelle": entry["libelle"],
                    "symbole": entry["symbole"],
                    "taux_reference": Decimal(str(entry.get("taux_reference"))) if entry.get("taux_reference") else None,
                    "actif": True,
                },
            )
            dev_map[entry["code_iso"]] = obj
        return dev_map

    def _seed_methodes_paiement(self):
        mp_map = {}
        for entry in METHODES_PAIEMENT_DATA:
            obj, _ = MethodePaiement.objects.update_or_create(
                code=entry["code"],
                defaults={
                    "libelle": entry["libelle"],
                    "description": entry.get("description", ""),
                    "actif": True,
                },
            )
            mp_map[entry["code"]] = obj
        return mp_map

    def _seed_categories(self):
        cat_map = {}
        for entry in CATEGORIES_DATA:
            obj, _ = Categorie.objects.update_or_create(
                code=entry["code"],
                defaults={"libelle": entry["libelle"], "actif": True},
            )
            cat_map[entry["code"]] = obj
        return cat_map

    def _seed_fournisseurs(self):
        f_map = {}
        for entry in FOURNISSEURS_DATA:
            obj, _ = Fournisseur.objects.update_or_create(
                code_fournisseur=entry["code_fournisseur"],
                defaults={
                    "raison_sociale": entry["raison_sociale"],
                    "email": entry.get("email", ""),
                    "description": entry.get("description", ""),
                    "actif": True,
                },
            )
            f_map[entry["code_fournisseur"]] = obj
        return f_map

    def _seed_banques(self):
        b_map = {}
        for entry in BANQUES_DATA:
            obj, _ = Banque.objects.update_or_create(
                code_banque=entry["code_banque"],
                defaults={
                    "nom": entry["nom"],
                    "code_swift": entry.get("code_swift", ""),
                    "adresse": entry.get("adresse", ""),
                    "actif": True,
                },
            )
            b_map[entry["code_banque"]] = obj
        return b_map

    def _seed_user(self, departement, role=None):
        User = get_user_model()
        user, created = User.objects.get_or_create(
            login="demoadmin",
            defaults={
                "email": "demo@example.com",
                "phone": "600000000",
                "first_name": "Demo",
                "last_name": "Admin",
                "id_departement": departement,
                "id_role": role,
                "is_staff": True,
                "is_superuser": False,
                "is_active": True,
            },
        )
        if created:
            user.set_password("password123")
            user.save()
        return user

    def _seed_roles(self):
        role_map = {}
        for entry in ROLES_DATA:
            obj, _ = Role.objects.update_or_create(
                code=entry["code"],
                defaults={"libelle": entry["libelle"], "description": entry.get("description", "")},
            )
            role_map[entry["code"]] = obj
        return role_map
