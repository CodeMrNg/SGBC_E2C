from django.db.models import Q
from rest_framework import filters

from ..models import (
    Article,
    Banque,
    BonCommande,
    Categorie,
    Demande,
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
    SignatureBC,
    SignatureNumerique,
)
from ..serializers.resources import (
    ArticleSerializer,
    BanqueSerializer,
    BonCommandeSerializer,
    CategorieSerializer,
    DemandeSerializer,
    DeviseSerializer,
    DocumentSerializer,
    FactureSerializer,
    FournisseurRIBSerializer,
    FournisseurSerializer,
    LigneBCSerializer,
    LigneBudgetaireSerializer,
    LigneDemandeSerializer,
    MethodePaiementSerializer,
    PaiementSerializer,
    SignatureBCSerializer,
    SignatureNumeriqueSerializer,
)
from .mixins import AuditModelViewSet


class DeviseViewSet(AuditModelViewSet):
    queryset = Devise.objects.all().order_by('code_iso')
    serializer_class = DeviseSerializer
    audit_prefix = 'devise'
    audit_type = 'DEVISE'

    def get_queryset(self):
        qs = super().get_queryset()
        code = self.request.GET.get('code_iso')
        actif = self.request.GET.get('actif')
        if code:
            qs = qs.filter(code_iso__icontains=code)
        if actif is not None:
            if actif.lower() in ['true', '1', 'yes']:
                qs = qs.filter(actif=True)
            elif actif.lower() in ['false', '0', 'no']:
                qs = qs.filter(actif=False)
        return qs


class MethodePaiementViewSet(AuditModelViewSet):
    queryset = MethodePaiement.objects.all().order_by('code')
    serializer_class = MethodePaiementSerializer
    audit_prefix = 'methode_paiement'
    audit_type = 'METHODE_PAIEMENT'

    def get_queryset(self):
        qs = super().get_queryset()
        code = self.request.GET.get('code')
        search = self.request.GET.get('search')
        if code:
            qs = qs.filter(code__icontains=code)
        if search:
            qs = qs.filter(Q(code__icontains=search) | Q(libelle__icontains=search) | Q(description__icontains=search))
        return qs


class CategorieViewSet(AuditModelViewSet):
    queryset = Categorie.objects.all().order_by('code')
    serializer_class = CategorieSerializer
    audit_prefix = 'categorie'
    audit_type = 'CATEGORIE'

    def get_queryset(self):
        qs = super().get_queryset()
        code = self.request.GET.get('code')
        search = self.request.GET.get('search')
        actif = self.request.GET.get('actif')
        if code:
            qs = qs.filter(code__icontains=code)
        if search:
            qs = qs.filter(Q(code__icontains=search) | Q(libelle__icontains=search))
        if actif is not None:
            qs = qs.filter(actif=actif.lower() in ['true', '1', 'yes'])
        return qs


class ArticleViewSet(AuditModelViewSet):
    queryset = Article.objects.select_related('id_categorie', 'id_devise').all().order_by('code_article')
    serializer_class = ArticleSerializer
    audit_prefix = 'article'
    audit_type = 'ARTICLE'

    def get_queryset(self):
        qs = super().get_queryset()
        code = self.request.GET.get('code_article')
        search = self.request.GET.get('search')
        categorie = self.request.GET.get('categorie_id')
        actif = self.request.GET.get('actif')
        if code:
            qs = qs.filter(code_article__icontains=code)
        if search:
            qs = qs.filter(Q(code_article__icontains=search) | Q(designation__icontains=search))
        if categorie:
            qs = qs.filter(id_categorie_id=categorie)
        if actif is not None:
            qs = qs.filter(actif=actif.lower() in ['true', '1', 'yes'])
        return qs


class FournisseurViewSet(AuditModelViewSet):
    queryset = Fournisseur.objects.all().order_by('code_fournisseur')
    serializer_class = FournisseurSerializer
    audit_prefix = 'fournisseur'
    audit_type = 'FOURNISSEUR'

    def get_queryset(self):
        qs = super().get_queryset()
        code = self.request.GET.get('code')
        search = self.request.GET.get('search')
        actif = self.request.GET.get('actif')
        if code:
            qs = qs.filter(code_fournisseur__icontains=code)
        if search:
            qs = qs.filter(
                Q(code_fournisseur__icontains=search)
                | Q(raison_sociale__icontains=search)
                | Q(description__icontains=search)
            )
        if actif is not None:
            qs = qs.filter(actif=actif.lower() in ['true', '1', 'yes'])
        return qs


class BanqueViewSet(AuditModelViewSet):
    queryset = Banque.objects.all().order_by('code_banque')
    serializer_class = BanqueSerializer
    audit_prefix = 'banque'
    audit_type = 'BANQUE'

    def get_queryset(self):
        qs = super().get_queryset()
        code = self.request.GET.get('code')
        search = self.request.GET.get('search')
        actif = self.request.GET.get('actif')
        if code:
            qs = qs.filter(code_banque__icontains=code)
        if search:
            qs = qs.filter(Q(code_banque__icontains=search) | Q(nom__icontains=search))
        if actif is not None:
            qs = qs.filter(actif=actif.lower() in ['true', '1', 'yes'])
        return qs


class FournisseurRIBViewSet(AuditModelViewSet):
    queryset = FournisseurRIB.objects.select_related('id_fournisseur', 'id_banque', 'id_devise').all().order_by('-date_creation')
    serializer_class = FournisseurRIBSerializer
    audit_prefix = 'fournisseur_rib'
    audit_type = 'FOURNISSEUR_RIB'

    def get_queryset(self):
        qs = super().get_queryset()
        fournisseur = self.request.GET.get('fournisseur_id')
        banque = self.request.GET.get('banque_id')
        actif = self.request.GET.get('actif')
        if fournisseur:
            qs = qs.filter(id_fournisseur_id=fournisseur)
        if banque:
            qs = qs.filter(id_banque_id=banque)
        if actif is not None:
            qs = qs.filter(actif=actif.lower() in ['true', '1', 'yes'])
        return qs


class DemandeViewSet(AuditModelViewSet):
    queryset = Demande.objects.select_related('id_departement').all().order_by('-date_creation')
    serializer_class = DemandeSerializer
    audit_prefix = 'demande'
    audit_type = 'DEMANDE'

    def get_queryset(self):
        qs = super().get_queryset()
        numero = self.request.GET.get('numero')
        statut = self.request.GET.get('statut')
        departement = self.request.GET.get('departement_id')
        search = self.request.GET.get('search')
        if numero:
            qs = qs.filter(numero_demande__icontains=numero)
        if statut:
            qs = qs.filter(statut_demande=statut)
        if departement:
            qs = qs.filter(id_departement_id=departement)
        if search:
            qs = qs.filter(Q(numero_demande__icontains=search) | Q(objet__icontains=search))
        return qs


class LigneDemandeViewSet(AuditModelViewSet):
    queryset = LigneDemande.objects.select_related('id_demande', 'id_article', 'id_fournisseur').all()
    serializer_class = LigneDemandeSerializer
    audit_prefix = 'ligne_demande'
    audit_type = 'LIGNE_DEMANDE'

    def get_queryset(self):
        qs = super().get_queryset()
        demande = self.request.GET.get('demande_id')
        article = self.request.GET.get('article_id')
        fournisseur = self.request.GET.get('fournisseur_id')
        if demande:
            qs = qs.filter(id_demande_id=demande)
        if article:
            qs = qs.filter(id_article_id=article)
        if fournisseur:
            qs = qs.filter(id_fournisseur_id=fournisseur)
        return qs


class LigneBudgetaireViewSet(AuditModelViewSet):
    queryset = LigneBudgetaire.objects.select_related('id_departement', 'id_devise').all()
    serializer_class = LigneBudgetaireSerializer
    audit_prefix = 'ligne_budgetaire'
    audit_type = 'LIGNE_BUDGETAIRE'

    def get_queryset(self):
        qs = super().get_queryset()
        code = self.request.GET.get('code')
        departement = self.request.GET.get('departement_id')
        exercice = self.request.GET.get('exercice')
        if code:
            qs = qs.filter(code_ligne__icontains=code)
        if departement:
            qs = qs.filter(id_departement_id=departement)
        if exercice:
            qs = qs.filter(exercice=exercice)
        return qs.order_by('code_ligne')


class DocumentViewSet(AuditModelViewSet):
    queryset = Document.objects.select_related('id_utilisateur').all().order_by('-date_generation')
    serializer_class = DocumentSerializer
    audit_prefix = 'document'
    audit_type = 'DOCUMENT'

    def get_queryset(self):
        qs = super().get_queryset()
        type_doc = self.request.GET.get('type_document')
        ref = self.request.GET.get('reference')
        user = self.request.GET.get('user_id')
        statut = self.request.GET.get('statut')
        if type_doc:
            qs = qs.filter(type_document=type_doc)
        if ref:
            qs = qs.filter(reference_fonctionnelle__icontains=ref)
        if user:
            qs = qs.filter(id_utilisateur_id=user)
        if statut:
            qs = qs.filter(statut_archivage=statut)
        return qs


class SignatureNumeriqueViewSet(AuditModelViewSet):
    queryset = SignatureNumerique.objects.select_related('id_document', 'id_utilisateur').all()
    serializer_class = SignatureNumeriqueSerializer
    audit_prefix = 'signature_numerique'
    audit_type = 'SIGNATURE_NUMERIQUE'

    def get_queryset(self):
        qs = super().get_queryset()
        document = self.request.GET.get('document_id')
        user = self.request.GET.get('user_id')
        if document:
            qs = qs.filter(id_document_id=document)
        if user:
            qs = qs.filter(id_utilisateur_id=user)
        return qs


class BonCommandeViewSet(AuditModelViewSet):
    queryset = BonCommande.objects.select_related(
        'id_demande',
        'id_fournisseur',
        'id_departement',
        'id_methode_paiement',
        'id_devise',
        'id_ligne_budgetaire',
        'id_redacteur',
        'id_demande_valider',
    ).all().order_by('-date_creation')
    serializer_class = BonCommandeSerializer
    audit_prefix = 'bon_commande'
    audit_type = 'BON_COMMANDE'

    def get_queryset(self):
        qs = super().get_queryset()
        numero = self.request.GET.get('numero')
        statut = self.request.GET.get('statut')
        fournisseur = self.request.GET.get('fournisseur_id')
        departement = self.request.GET.get('departement_id')
        if numero:
            qs = qs.filter(numero_bc__icontains=numero)
        if statut:
            qs = qs.filter(statut_bc=statut)
        if fournisseur:
            qs = qs.filter(id_fournisseur_id=fournisseur)
        if departement:
            qs = qs.filter(id_departement_id=departement)
        return qs


class LigneBCViewSet(AuditModelViewSet):
    queryset = LigneBC.objects.select_related('id_bc', 'id_article', 'id_devise').all()
    serializer_class = LigneBCSerializer
    audit_prefix = 'ligne_bc'
    audit_type = 'LIGNE_BC'

    def get_queryset(self):
        qs = super().get_queryset()
        bc = self.request.GET.get('bc_id')
        article = self.request.GET.get('article_id')
        if bc:
            qs = qs.filter(id_bc_id=bc)
        if article:
            qs = qs.filter(id_article_id=article)
        return qs


class SignatureBCViewSet(AuditModelViewSet):
    queryset = SignatureBC.objects.select_related('id_bc', 'id_signataire', 'id_document_preuve').all()
    serializer_class = SignatureBCSerializer
    audit_prefix = 'signature_bc'
    audit_type = 'SIGNATURE_BC'

    def get_queryset(self):
        qs = super().get_queryset()
        bc = self.request.GET.get('bc_id')
        signataire = self.request.GET.get('signataire_id')
        if bc:
            qs = qs.filter(id_bc_id=bc)
        if signataire:
            qs = qs.filter(id_signataire_id=signataire)
        return qs


class FactureViewSet(AuditModelViewSet):
    queryset = Facture.objects.select_related('id_bc', 'id_devise', 'id_document_facture', 'id_agent_comptable').all()
    serializer_class = FactureSerializer
    audit_prefix = 'facture'
    audit_type = 'FACTURE'

    def get_queryset(self):
        qs = super().get_queryset()
        numero = self.request.GET.get('numero')
        bc = self.request.GET.get('bc_id')
        statut = self.request.GET.get('statut')
        if numero:
            qs = qs.filter(numero_facture__icontains=numero)
        if bc:
            qs = qs.filter(id_bc_id=bc)
        if statut:
            qs = qs.filter(statut_facture=statut)
        return qs


class PaiementViewSet(AuditModelViewSet):
    queryset = Paiement.objects.select_related(
        'id_facture', 'id_banque', 'id_methode_paiement', 'id_preuve_paiement', 'id_tresorier'
    ).all()
    serializer_class = PaiementSerializer
    audit_prefix = 'paiement'
    audit_type = 'PAIEMENT'

    def get_queryset(self):
        qs = super().get_queryset()
        facture = self.request.GET.get('facture_id')
        statut = self.request.GET.get('statut')
        banque = self.request.GET.get('banque_id')
        if facture:
            qs = qs.filter(id_facture_id=facture)
        if banque:
            qs = qs.filter(id_banque_id=banque)
        if statut:
            qs = qs.filter(statut_paiement=statut)
        return qs
