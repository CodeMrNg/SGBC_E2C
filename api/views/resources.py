from django.db import models, transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.views import APIView
from rest_framework.response import Response

from ..auth_utils import log_audit
from ..models import (
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
    SignatureBC,
    SignatureNumerique,
    Transfert,
)
from ..models.bon_commande import StatutBC
from ..models.demandes import StatutDemande
from ..models.transferts import StatutTransfert
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
    TransfertSerializer,
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
    queryset = Demande.objects.select_related('id_departement').prefetch_related(
        'lignes__id_article',
        'lignes__id_fournisseur',
        'documents',
    ).all().order_by('-date_creation')
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
            statut_normalise = {
                'en_cours': StatutDemande.EN_TRAITEMENT,
                'rejecter': StatutDemande.REJETER,
                'bouillon': StatutDemande.BROUILLON,
            }.get(statut, statut)
            qs = qs.filter(statut_demande=statut_normalise)
        if departement:
            qs = qs.filter(id_departement_id=departement)
        if search:
            qs = qs.filter(Q(numero_demande__icontains=search) | Q(objet__icontains=search))
        return qs

    @action(detail=True, methods=['post'], url_path='transfer')
    def transfer(self, request, pk=None):
        departement_id = request.data.get('departement_id')
        raison = (request.data.get('raison') or '').strip()
        if not departement_id:
            return Response(
                {'detail': 'Le champ departement_id est requis.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not raison:
            return Response(
                {'detail': 'Le champ raison est requis.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        departement = get_object_or_404(Departement, pk=departement_id)
        demande = self.get_object()

        if demande.id_departement_id == departement.id:
            return Response(
                {'detail': 'La demande est déjà rattachée à ce département.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        departement_source = demande.id_departement
        with transaction.atomic():
            demande.id_departement = departement
            demande.save(update_fields=['id_departement'])
            Transfert.objects.create(
                departement_source=departement_source,
                departement_beneficiaire=departement,
                statut=StatutTransfert.VALIDE,
                raison=raison,
                agent=request.user,
                id_demande=demande,
            )
            log_audit(
                request.user,
                'demande_transfer',
                type_objet=self.audit_type,
                id_objet=demande.id,
                request=request,
                details=f'Transfert vers le département {departement.id} | raison: {raison}',
            )

        serializer = self.get_serializer(demande)
        return Response(serializer.data, status=status.HTTP_200_OK)


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


class TransfertViewSet(AuditModelViewSet):
    queryset = Transfert.objects.select_related(
        'departement_source',
        'departement_beneficiaire',
        'agent',
        'id_demande',
        'id_bc',
    ).all().order_by('-date_transfert')
    serializer_class = TransfertSerializer
    audit_prefix = 'transfert'
    audit_type = 'TRANSFERT'

    def get_queryset(self):
        qs = super().get_queryset()
        demande = self.request.GET.get('demande_id')
        bc = self.request.GET.get('bc_id')
        source = self.request.GET.get('departement_source_id')
        beneficiaire = self.request.GET.get('departement_beneficiaire_id')
        agent = self.request.GET.get('agent_id')
        statut = self.request.GET.get('statut')
        if demande:
            qs = qs.filter(id_demande_id=demande)
        if bc:
            qs = qs.filter(id_bc_id=bc)
        if source:
            qs = qs.filter(departement_source_id=source)
        if beneficiaire:
            qs = qs.filter(departement_beneficiaire_id=beneficiaire)
        if agent:
            qs = qs.filter(agent_id=agent)
        if statut:
            qs = qs.filter(statut=statut)
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
    ).prefetch_related(
        'lignes__id_article',
        'lignes__id_devise',
        'documents',
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
            statut_normalise = {
                'en_redaction': StatutBC.EN_ATTENTE,
                'en_signature': StatutBC.EN_TRAITEMENT,
                'signe': StatutBC.VALIDER,
                'envoye': StatutBC.VALIDER,
                'receptionne': StatutBC.VALIDER,
            }.get(statut, statut)
            qs = qs.filter(statut_bc=statut_normalise)
        if fournisseur:
            qs = qs.filter(id_fournisseur_id=fournisseur)
        if departement:
            qs = qs.filter(id_departement_id=departement)
        return qs


class DashboardView(APIView):
    """
    Endpoint de synthèse : métriques et dernières demandes/BC.
    """

    def get(self, request, format=None):
        demandes_qs = Demande.objects.select_related('id_departement').prefetch_related('lignes', 'documents')
        bc_qs = BonCommande.objects.select_related(
            'id_demande',
            'id_fournisseur',
            'id_departement',
            'id_methode_paiement',
            'id_devise',
            'id_ligne_budgetaire',
            'id_redacteur',
            'id_demande_valider',
        ).prefetch_related('lignes', 'documents')

        demande_par_statut = dict(
            demandes_qs.values_list('statut_demande').annotate(total=models.Count('id'))
        )
        bc_par_statut = dict(bc_qs.values_list('statut_bc').annotate(total=models.Count('id')))

        demandes_by_status = {}
        for key, statut in {
            'en_attente': StatutDemande.EN_ATTENTE,
            'en_traitement': StatutDemande.EN_TRAITEMENT,
            'en_cours': StatutDemande.EN_TRAITEMENT,  # alias compat
            'valider': StatutDemande.VALIDER,
            'rejeter': StatutDemande.REJETER,
        }.items():
            demandes_by_status[key] = DemandeSerializer(
                demandes_qs.filter(statut_demande=statut).order_by('-date_creation')[:5],
                many=True,
            ).data

        bc_by_status = {}
        for key, statut in {
            'en_attente': StatutBC.EN_ATTENTE,
            'en_traitement': StatutBC.EN_TRAITEMENT,
            'en_cours': StatutBC.EN_TRAITEMENT,  # alias compat
            'valider': StatutBC.VALIDER,
        }.items():
            bc_by_status[key] = BonCommandeSerializer(
                bc_qs.filter(statut_bc=statut).order_by('-date_creation')[:5],
                many=True,
            ).data

        data = {
            'metrics': {
                'demandes_total': demandes_qs.count(),
                'demandes_par_statut': demande_par_statut,
                'bons_commande_total': bc_qs.count(),
                'bons_commande_par_statut': bc_par_statut,
                'lignes_demande_total': LigneDemande.objects.count(),
                'lignes_bc_total': LigneBC.objects.count(),
                'documents_total': Document.objects.count(),
                'transferts_total': Transfert.objects.count(),
                'factures_total': Facture.objects.count(),
                'paiements_total': Paiement.objects.count(),
                'fournisseurs_total': Fournisseur.objects.count(),
                'articles_total': Article.objects.count(),
                'devises_total': Devise.objects.count(),
                'departements_total': Departement.objects.count(),
                'categories_total': Categorie.objects.count(),
                'methodes_paiement_total': MethodePaiement.objects.count(),
                'banques_total': Banque.objects.count(),
                'fournisseurs_rib_total': FournisseurRIB.objects.count(),
                'signatures_numeriques_total': SignatureNumerique.objects.count(),
                'signatures_bc_total': SignatureBC.objects.count(),
                'lignes_budgetaires_total': LigneBudgetaire.objects.count(),
            },
            'dernieres_demandes': DemandeSerializer(
                demandes_qs.order_by('-date_creation')[:5],
                many=True,
            ).data,
            'derniers_bons_commande': BonCommandeSerializer(
                bc_qs.order_by('-date_creation')[:5],
                many=True,
            ).data,
            'dernieres_demandes_par_statut': demandes_by_status,
            'derniers_bons_commande_par_statut': bc_by_status,
        }
        return Response(data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='transfer')
    def transfer(self, request, pk=None):
        departement_id = request.data.get('departement_id')
        raison = (request.data.get('raison') or '').strip()
        if not departement_id:
            return Response(
                {'detail': 'Le champ departement_id est requis.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not raison:
            return Response(
                {'detail': 'Le champ raison est requis.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        departement = get_object_or_404(Departement, pk=departement_id)
        bc = self.get_object()

        if bc.id_departement_id == departement.id:
            return Response(
                {'detail': 'Le bon de commande est déjà rattaché à ce département.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        departement_source = bc.id_departement
        with transaction.atomic():
            bc.id_departement = departement
            bc.save(update_fields=['id_departement'])
            demande_updated = False
            if bc.id_demande and bc.id_demande.id_departement_id != departement.id:
                bc.id_demande.id_departement = departement
                bc.id_demande.save(update_fields=['id_departement'])
                demande_updated = True
            Transfert.objects.create(
                departement_source=departement_source,
                departement_beneficiaire=departement,
                statut=StatutTransfert.VALIDE,
                raison=raison,
                agent=request.user,
                id_bc=bc,
                id_demande=bc.id_demande,
            )

            log_audit(
                request.user,
                'bon_commande_transfer',
                type_objet=self.audit_type,
                id_objet=bc.id,
                request=request,
                details=(
                    f'Transfert vers le département {departement.id}'
                    + (' avec mise à jour de la demande liée' if demande_updated else '')
                    + f' | raison: {raison}'
                ),
            )

        serializer = self.get_serializer(bc)
        return Response(serializer.data, status=status.HTTP_200_OK)


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
