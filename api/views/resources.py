from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.db import models, transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.views import APIView
from rest_framework.response import Response

from .mixins import AuditModelViewSet
from ..auth_utils import log_audit
from ..models import (
    Article,
    AuditLog,
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
    Utilisateur,
)
from ..models.bon_commande import DecisionSignature, StatutBC
from ..models.demandes import DecisionDemande, StatutDemande
from ..models.documents import StatutArchivage
from ..models.facturation_paiement import StatutFacture, StatutPaiement
from ..models.transferts import StatutTransfert
from ..serializers.audit import AuditLogSerializer
from ..serializers.auth import UserSerializer
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

SUPER_ADMIN_ROLES = {'SAD', 'SD', 'DAA', 'BUDGET', 'DFC', 'TRESOR'}


def _user_role_code(user) -> str:
    return (getattr(getattr(user, 'id_role', None), 'code', '') or '').strip().upper()


def user_is_sad(user) -> bool:
    return _user_role_code(user) == 'SAD'


def user_is_sd(user) -> bool:
    return _user_role_code(user) == 'SD'


def user_has_global_access(user) -> bool:
    # Global sauf cas spécifique géré par les filtres dédiés (ex: demandes/BC pour SD).
    return _user_role_code(user) in SUPER_ADMIN_ROLES


def user_departement_id(user):
    departement = getattr(user, 'id_departement', None)
    return getattr(departement, 'id', None)


def filter_by_departement(qs, user, field_name: str):
    """
    Restreint un queryset au département de l'utilisateur connecté,
    sauf pour les rôles globaux (SAD/SD/superuser).
    """
    if user_has_global_access(user):
        return qs
    departement_id = user_departement_id(user)
    if not departement_id:
        return qs.none()
    return qs.filter(**{field_name: departement_id})


def filter_transferts_for_user(qs, user):
    if user_has_global_access(user):
        return qs
    departement_id = user_departement_id(user)
    if not departement_id:
        return qs.none()
    return qs.filter(
        Q(departement_source_id=departement_id)
        | Q(departement_beneficiaire_id=departement_id)
        | Q(id_demande__id_departement_id=departement_id)
        | Q(id_bc__id_departement_id=departement_id)
    )


def filter_demandes_for_user(qs, user):
    if user_has_global_access(user):
        return qs
    departement_id = user_departement_id(user)
    has_user_access = bool(user and getattr(user, 'is_authenticated', False))
    transfert_filter = Q(utilisateurs_transferts=user) if has_user_access else Q(pk__isnull=True)
    dept_qs = filter_by_departement(qs, user, 'id_departement_id')
    if not user:
        return dept_qs
    return (dept_qs | qs.filter(transfert_filter)).distinct()


def filter_bc_for_user(qs, user):
    if user_has_global_access(user):
        return qs
    departement_id = user_departement_id(user)
    if user_is_sd(user):
        brouillon_filter = ~Q(id_demande__statut_demande=StatutDemande.BROUILLON)
        if departement_id:
            return qs.filter(brouillon_filter | Q(id_departement_id=departement_id))
        return qs.filter(brouillon_filter)
    return filter_by_departement(qs, user, 'id_departement_id')


def _quantize_money(value: Decimal) -> Decimal:
    return value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)


def _safe_decimal(value) -> Decimal:
    if value in [None, '', 'null']:
        return Decimal('0')
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return Decimal('0')


def _compute_montant_engage(bc) -> Decimal:
    if not bc:
        return Decimal('0')
    total = Decimal('0')
    bc_tva = _safe_decimal(getattr(bc, 'tva', None))
    for ligne in bc.lignes.all():
        base = _safe_decimal(ligne.quantite) * _safe_decimal(ligne.prix_unitaire)
        taux_tva = _safe_decimal(ligne.taux_tva) if ligne.taux_tva is not None else bc_tva
        tva_amount = base * (taux_tva / Decimal('100')) if taux_tva else Decimal('0')
        ca_amount = _safe_decimal(ligne.ca)
        total += base + tva_amount + ca_amount
    return _quantize_money(total)


def _update_bc_montant_engage(bc) -> None:
    if not bc:
        return
    bc.montant_engage = _compute_montant_engage(bc)
    bc.save(update_fields=['montant_engage'])


def _paiement_totaux(bc):
    total_autorise = bc.montant_engage or Decimal('0')
    if total_autorise <= 0:
        total_autorise = (
            bc.factures.aggregate(total=models.Sum('montant_ttc')).get('total') or Decimal('0')
        )
    total_paye = (
        Paiement.objects.filter(id_facture__id_bc=bc).aggregate(total=models.Sum('montant')).get('total')
        or Decimal('0')
    )
    return total_autorise, total_paye


def build_history_response(viewset, type_objet: str, obj_id):
    """
    Rassemble l'historique d'actions pour un objet donnÇ¸ avec
    des champs simples (nom, prÇ¸nom, dÇ¸partement, action, horodatage, dÇ¸tails).
    """
    logs = (
        AuditLog.objects.select_related('id_utilisateur')
        .filter(type_objet=type_objet, id_objet=obj_id)
        .order_by('-timestamp')
    )
    history = []
    for log in logs:
        user = getattr(log, 'id_utilisateur', None)
        departement = getattr(getattr(user, 'id_departement', None), 'nom', None)
        raw_details = (log.details or '').strip()
        action_label = {
            'create': 'Création',
            'update': 'Mise à jour',
            'delete': 'Suppression',
        }.get(log.action, f'Action {log.action}')
        description = raw_details or action_label
        history.append(
            {
                'nom': getattr(user, 'last_name', None) if user else None,
                'prenom': getattr(user, 'first_name', None) if user else None,
                'departement': departement,
                'action': log.action,
                'details': description,
                'timestamp': log.timestamp,
            }
        )
    return Response(
        {
            'message': 'Historique récupéré avec succès',
            'data': {'historique': history},
        },
        status=status.HTTP_200_OK,
    )


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

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        qs = self.filter_queryset(self.get_queryset())
        counts = dict(qs.values_list('actif').annotate(total=models.Count('id')))
        data = {
            'total': qs.count(),
            'actifs': counts.get(True, 0),
            'inactifs': counts.get(False, 0),
            'derniers': self.get_serializer(qs.order_by('-id')[:5], many=True).data,
            'a_traiter': self.get_serializer(qs.filter(actif=False).order_by('-id')[:5], many=True).data,
        }
        return Response({'message': 'Statistiques des devises', 'data': data}, status=status.HTTP_200_OK)


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

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        qs = self.filter_queryset(self.get_queryset())
        counts = dict(qs.values_list('actif').annotate(total=models.Count('id')))
        data = {
            'total': qs.count(),
            'actifs': counts.get(True, 0),
            'inactifs': counts.get(False, 0),
            'derniers': self.get_serializer(qs.order_by('-id')[:5], many=True).data,
            'a_traiter': self.get_serializer(qs.filter(actif=False).order_by('-id')[:5], many=True).data,
        }
        return Response({'message': 'Statistiques des méthodes de paiement', 'data': data}, status=status.HTTP_200_OK)


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

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        qs = self.filter_queryset(self.get_queryset())
        counts = dict(qs.values_list('actif').annotate(total=models.Count('id')))
        data = {
            'total': qs.count(),
            'actifs': counts.get(True, 0),
            'inactifs': counts.get(False, 0),
            'derniers': self.get_serializer(qs.order_by('-id')[:5], many=True).data,
            'a_traiter': self.get_serializer(qs.filter(actif=False).order_by('-id')[:5], many=True).data,
        }
        return Response({'message': 'Statistiques des catégories', 'data': data}, status=status.HTTP_200_OK)


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
        type_article = self.request.GET.get('type_article')
        actif = self.request.GET.get('actif')
        if code:
            qs = qs.filter(code_article__icontains=code)
        if search:
            qs = qs.filter(Q(code_article__icontains=search) | Q(designation__icontains=search))
        if categorie:
            qs = qs.filter(id_categorie_id=categorie)
        if type_article:
            qs = qs.filter(type_article=type_article)
        if actif is not None:
            qs = qs.filter(actif=actif.lower() in ['true', '1', 'yes'])
        return qs

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        qs = self.filter_queryset(self.get_queryset())
        counts = dict(qs.values_list('actif').annotate(total=models.Count('id')))
        data = {
            'total': qs.count(),
            'actifs': counts.get(True, 0),
            'inactifs': counts.get(False, 0),
            'derniers': self.get_serializer(qs.order_by('-id')[:5], many=True).data,
            'a_traiter': self.get_serializer(qs.filter(actif=False).order_by('-id')[:5], many=True).data,
        }
        return Response({'message': 'Statistiques des articles', 'data': data}, status=status.HTTP_200_OK)


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

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        qs = self.filter_queryset(self.get_queryset())
        counts = dict(qs.values_list('actif').annotate(total=models.Count('id')))
        data = {
            'total': qs.count(),
            'actifs': counts.get(True, 0),
            'inactifs': counts.get(False, 0),
            'derniers': self.get_serializer(qs.order_by('-id')[:5], many=True).data,
            'a_traiter': self.get_serializer(qs.filter(actif=False).order_by('-id')[:5], many=True).data,
        }
        return Response({'message': 'Statistiques des fournisseurs', 'data': data}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='associations')
    def associations(self, request, pk=None):
        fournisseur = self.get_object()
        demandes_qs = (
            Demande.objects.select_related('id_departement', 'agent_traitant', 'id_fournisseur')
            .prefetch_related('lignes__id_article', 'documents')
            .filter(id_fournisseur=fournisseur)
            .distinct()
            .order_by('-date_creation')
        )
        bc_qs = (
            BonCommande.objects.select_related(
                'id_demande',
                'id_fournisseur',
                'id_departement',
                'agent_traitant',
                'id_methode_paiement',
                'id_devise',
                'id_redacteur',
                'id_demande_valider',
            )
            .prefetch_related('lignes__id_article', 'lignes__id_devise', 'documents')
            .filter(id_fournisseur=fournisseur)
            .order_by('-date_creation')
        )
        demandes_qs = filter_demandes_for_user(demandes_qs, request.user)
        bc_qs = filter_bc_for_user(bc_qs, request.user)
        data = {
            'fournisseur': self.get_serializer(fournisseur).data,
            'demandes': DemandeSerializer(demandes_qs, many=True, context=self.get_serializer_context()).data,
            'bons_commande': BonCommandeSerializer(bc_qs, many=True, context=self.get_serializer_context()).data,
        }
        return Response({'message': 'Associations fournisseur', 'data': data}, status=status.HTTP_200_OK)


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

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        qs = self.filter_queryset(self.get_queryset())
        counts = dict(qs.values_list('actif').annotate(total=models.Count('id')))
        data = {
            'total': qs.count(),
            'actifs': counts.get(True, 0),
            'inactifs': counts.get(False, 0),
            'derniers': self.get_serializer(qs.order_by('-id')[:5], many=True).data,
            'a_traiter': self.get_serializer(qs.filter(actif=False).order_by('-id')[:5], many=True).data,
        }
        return Response({'message': 'Statistiques des banques', 'data': data}, status=status.HTTP_200_OK)


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

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        qs = self.filter_queryset(self.get_queryset())
        counts = dict(qs.values_list('actif').annotate(total=models.Count('id')))
        data = {
            'total': qs.count(),
            'actifs': counts.get(True, 0),
            'inactifs': counts.get(False, 0),
            'derniers': self.get_serializer(qs.order_by('-date_creation')[:5], many=True).data,
            'a_traiter': self.get_serializer(qs.filter(actif=False).order_by('-date_creation')[:5], many=True).data,
        }
        return Response({'message': 'Statistiques des RIB fournisseurs', 'data': data}, status=status.HTTP_200_OK)


class DemandeViewSet(AuditModelViewSet):
    queryset = Demande.objects.select_related('id_departement', 'agent_traitant', 'id_fournisseur').prefetch_related(
        'lignes__id_article',
        'documents',
        'utilisateurs_transferts',
        models.Prefetch(
            'transferts',
            queryset=Transfert.objects.select_related(
                'departement_source',
                'departement_beneficiaire',
                'agent',
            ),
        ),
    ).all().order_by('-date_creation')
    serializer_class = DemandeSerializer
    audit_prefix = 'demande'
    audit_type = 'DEMANDE'

    def get_queryset(self):
        qs = super().get_queryset()
        numero = self.request.GET.get('numero')
        statut = self.request.GET.get('statut')
        departement = self.request.GET.get('departement_id')
        fournisseur = self.request.GET.get('fournisseur_id')
        search = self.request.GET.get('search')
        date_debut = self.request.GET.get('date_debut') or self.request.GET.get('date_from')
        date_fin = self.request.GET.get('date_fin') or self.request.GET.get('date_to')
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
        if fournisseur:
            qs = qs.filter(id_fournisseur_id=fournisseur)
        if date_debut:
            parsed = parse_date(date_debut)
            if parsed:
                qs = qs.filter(date_creation__date__gte=parsed)
        if date_fin:
            parsed = parse_date(date_fin)
            if parsed:
                qs = qs.filter(date_creation__date__lte=parsed)
        if search:
            qs = qs.filter(Q(numero_demande__icontains=search) | Q(objet__icontains=search))
        return filter_demandes_for_user(qs, self.request.user)

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        qs = self.filter_queryset(self.get_queryset())
        counts = dict(qs.values_list('statut_demande').annotate(total=models.Count('id')))
        data = {
            'total': qs.count(),
            'en_attente': counts.get(StatutDemande.EN_ATTENTE, 0),
            'en_traitement': counts.get(StatutDemande.EN_TRAITEMENT, 0),
            'valider': counts.get(StatutDemande.VALIDER, 0),
            'rejeter': counts.get(StatutDemande.REJETER, 0),
            'dernieres': self.get_serializer(qs.order_by('-date_creation')[:5], many=True).data,
            'a_traiter': self.get_serializer(
                qs.filter(statut_demande__in=[StatutDemande.EN_ATTENTE, StatutDemande.EN_TRAITEMENT])
                .order_by('-date_creation')[:5],
                many=True,
            ).data,
        }
        return Response({'message': 'Statistiques des demandes', 'data': data}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='history')
    def history(self, request, pk=None):
        demande = self.get_object()
        return build_history_response(self, self.audit_type, demande.id)

    @action(detail=True, methods=['post'], url_path='assign-agent')
    def assign_agent(self, request, pk=None):
        agent_id = request.data.get('agent_id') or request.data.get('agent_traitant_id')
        demande = self.get_object()
        if agent_id in [None, '', 'null']:
            demande.agent_traitant = None
            demande.save(update_fields=['agent_traitant'])
            log_audit(
                request.user,
                'demande_assign_agent',
                type_objet=self.audit_type,
                id_objet=demande.id,
                request=request,
                details='Agent traitant retiré',
            )
            serializer = self.get_serializer(demande)
            return Response(
                {'message': 'Agent traitant retiré avec succès', 'data': serializer.data},
                status=status.HTTP_200_OK,
            )

        agent = get_object_or_404(Utilisateur, pk=agent_id)
        demande.agent_traitant = agent
        demande.save(update_fields=['agent_traitant'])
        log_audit(
            request.user,
            'demande_assign_agent',
            type_objet=self.audit_type,
            id_objet=demande.id,
            request=request,
            details=f'Agent traitant défini: {agent.id}',
        )
        serializer = self.get_serializer(demande)
        return Response(
            {'message': 'Agent traitant mis à jour avec succès', 'data': serializer.data},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['post'], url_path='signature')
    def signature(self, request, pk=None):
        demande = self.get_object()
        decision = (request.data.get('decision') or '').strip().lower()
        if not decision:
            return Response(
                {'message': 'Validation echouee', 'detail': 'Le champ decision est requis.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if decision not in DecisionDemande.values:
            return Response(
                {'message': 'Validation echouee', 'detail': 'Decision invalide.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        signataire_id = (
            request.data.get('signataire_id')
            or request.data.get('user_id')
            or request.data.get('id_signataire')
        )
        if signataire_id in [None, '', 'null']:
            signataire = request.user if getattr(request.user, 'id', None) else None
            if not signataire:
                return Response(
                    {'message': 'Validation echouee', 'detail': 'Signataire requis.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            signataire = get_object_or_404(Utilisateur, pk=signataire_id)

        document_preuve_id = request.data.get('document_preuve_id') or request.data.get('id_document_preuve')
        if document_preuve_id in [None, '', 'null']:
            document_preuve = None
        else:
            document_preuve = get_object_or_404(Document, pk=document_preuve_id)

        commentaire = (request.data.get('commentaire') or request.data.get('comment') or '').strip()

        demande.id_signataire = signataire
        demande.decision = decision
        demande.commentaire = commentaire
        demande.id_document_preuve = document_preuve
        demande.date_signature = timezone.now()

        update_fields = [
            'id_signataire',
            'decision',
            'commentaire',
            'id_document_preuve',
            'date_signature',
        ]
        if decision == DecisionDemande.APPROUVE:
            demande.statut_demande = StatutDemande.VALIDER
            update_fields.append('statut_demande')
        elif decision == DecisionDemande.REFUSE:
            demande.statut_demande = StatutDemande.REJETER
            update_fields.append('statut_demande')

        demande.save(update_fields=update_fields)
        log_audit(
            request.user,
            'demande_signature',
            type_objet=self.audit_type,
            id_objet=demande.id,
            request=request,
            details=f'Decision: {decision}',
        )
        serializer = self.get_serializer(demande)
        return Response(
            {'message': 'Signature de demande enregistree', 'data': serializer.data},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['post'], url_path='transfer')
    def transfer(self, request, pk=None):
        departement_id = request.data.get('departement_id')
        raison = (request.data.get('raison') or '').strip()
        if not departement_id:
            return Response(
                {'message': 'Validation échouée', 'detail': 'Le champ departement_id est requis.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not raison:
            return Response(
                {'message': 'Validation échouée', 'detail': 'Le champ raison est requis.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        departement = get_object_or_404(Departement, pk=departement_id)
        demande = self.get_object()

        if demande.id_departement_id == departement.id:
            return Response(
                {'message': 'Validation échouée', 'detail': 'La demande est déjà rattachée à ce département.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        last_transfer = demande.transferts.order_by('-date_transfert').first()
        departement_source = last_transfer.departement_beneficiaire if last_transfer else demande.id_departement
        with transaction.atomic():
            demande.id_departement = departement
            demande.agent_traitant_id = None
            demande.save(update_fields=['id_departement', 'agent_traitant'])
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
                details=f'Transfert vers le département {departement.nom} | raison: {raison}',
            )

        serializer = self.get_serializer(demande)
        return Response(
            {'message': 'Transfert de demande effectué avec succès', 'data': serializer.data},
            status=status.HTTP_200_OK,
        )


class LigneDemandeViewSet(AuditModelViewSet):
    queryset = LigneDemande.objects.select_related('id_demande', 'id_article').all()
    serializer_class = LigneDemandeSerializer
    audit_prefix = 'ligne_demande'
    audit_type = 'LIGNE_DEMANDE'

    def get_queryset(self):
        qs = super().get_queryset()
        demande = self.request.GET.get('demande_id')
        article = self.request.GET.get('article_id')
        if demande:
            qs = qs.filter(id_demande_id=demande)
        if article:
            qs = qs.filter(id_article_id=article)
        return filter_by_departement(qs, self.request.user, 'id_demande__id_departement_id')

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        qs = self.filter_queryset(self.get_queryset())
        data = {
            'total': qs.count(),
            'derniers': self.get_serializer(qs.order_by('-id')[:5], many=True).data,
            'a_traiter': [],
        }
        return Response({'message': 'Statistiques des lignes de demande', 'data': data}, status=status.HTTP_200_OK)


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
        qs = qs.order_by('code_ligne')
        return filter_by_departement(qs, self.request.user, 'id_departement_id')

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        qs = self.filter_queryset(self.get_queryset())
        data = {
            'total': qs.count(),
            'derniers': self.get_serializer(qs.order_by('-exercice', '-code_ligne')[:5], many=True).data,
            'a_traiter': [],
        }
        return Response({'message': 'Statistiques des lignes budgétaires', 'data': data}, status=status.HTTP_200_OK)


class DocumentViewSet(AuditModelViewSet):
    queryset = Document.objects.select_related('id_utilisateur').all().order_by('-date_generation')
    serializer_class = DocumentSerializer
    audit_prefix = 'document'
    audit_type = 'DOCUMENT'
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def perform_create(self, serializer):
        instance = serializer.save(id_utilisateur=self.request.user)
        log_audit(
            self.request.user,
            f'{self.audit_prefix}_create',
            type_objet=self.audit_type,
            id_objet=instance.id,
            request=self.request,
        )

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
        return filter_by_departement(qs, self.request.user, 'id_utilisateur__id_departement_id')

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        qs = self.filter_queryset(self.get_queryset())
        counts = dict(qs.values_list('statut_archivage').annotate(total=models.Count('id')))
        data = {
            'total': qs.count(),
            'actif': counts.get(StatutArchivage.ACTIF, 0),
            'archive': counts.get(StatutArchivage.ARCHIVE, 0),
            'derniers': self.get_serializer(qs.order_by('-date_generation')[:5], many=True).data,
            'a_traiter': [],
        }
        return Response({'message': 'Statistiques des documents', 'data': data}, status=status.HTTP_200_OK)


class SignatureNumeriqueViewSet(AuditModelViewSet):
    queryset = SignatureNumerique.objects.select_related(
        'id_document',
        'id_utilisateur',
        'id_utilisateur__signature_utilisateur',
    ).all()
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

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        qs = self.filter_queryset(self.get_queryset())
        data = {
            'total': qs.count(),
            'derniers': self.get_serializer(qs.order_by('-date_signature')[:5], many=True).data,
            'a_traiter': [],
        }
        return Response({'message': 'Statistiques des signatures numériques', 'data': data}, status=status.HTTP_200_OK)


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
        return filter_transferts_for_user(qs, self.request.user)

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        qs = self.filter_queryset(self.get_queryset())
        counts = dict(qs.values_list('statut').annotate(total=models.Count('id')))
        data = {
            'total': qs.count(),
            'valide': counts.get(StatutTransfert.VALIDE, 0),
            'rejete': counts.get(StatutTransfert.REJETE, 0),
            'derniers': self.get_serializer(qs.order_by('-date_transfert')[:5], many=True).data,
            'a_traiter': [],
        }
        return Response({'message': 'Statistiques des transferts', 'data': data}, status=status.HTTP_200_OK)


class BonCommandeViewSet(AuditModelViewSet):
    queryset = BonCommande.objects.select_related(
        'id_demande',
        'id_fournisseur',
        'id_departement',
        'agent_traitant',
        'id_methode_paiement',
        'id_devise',
        'id_redacteur',
        'id_demande_valider',
    ).prefetch_related(
        'lignes__id_article',
        'lignes__id_devise',
        'documents',
        models.Prefetch(
            'signatures',
            queryset=SignatureBC.objects.select_related('id_signataire', 'id_document_preuve'),
        ),
        models.Prefetch(
            'transferts',
            queryset=Transfert.objects.select_related(
                'departement_source',
                'departement_beneficiaire',
                'agent',
            ),
        ),
    ).all().order_by('-date_creation')
    serializer_class = BonCommandeSerializer
    audit_prefix = 'bon_commande'
    audit_type = 'BON_COMMANDE'

    def perform_create(self, serializer):
        super().perform_create(serializer)
        _update_bc_montant_engage(serializer.instance)

    def perform_update(self, serializer):
        super().perform_update(serializer)
        _update_bc_montant_engage(serializer.instance)

    def get_queryset(self):
        qs = super().get_queryset()
        numero = self.request.GET.get('numero')
        statut = self.request.GET.get('statut')
        fournisseur = self.request.GET.get('fournisseur_id')
        departement = self.request.GET.get('departement_id')
        date_debut = self.request.GET.get('date_debut') or self.request.GET.get('date_from')
        date_fin = self.request.GET.get('date_fin') or self.request.GET.get('date_to')
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
        if date_debut:
            parsed = parse_date(date_debut)
            if parsed:
                qs = qs.filter(date_creation__date__gte=parsed)
        if date_fin:
            parsed = parse_date(date_fin)
            if parsed:
                qs = qs.filter(date_creation__date__lte=parsed)
        return filter_bc_for_user(qs, self.request.user)

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        qs = self.filter_queryset(self.get_queryset())
        counts = dict(qs.values_list('statut_bc').annotate(total=models.Count('id')))
        data = {
            'total': qs.count(),
            'en_attente': counts.get(StatutBC.EN_ATTENTE, 0),
            'en_traitement': counts.get(StatutBC.EN_TRAITEMENT, 0),
            'valider': counts.get(StatutBC.VALIDER, 0),
            'rejeter': counts.get('rejeter', 0),  # statut non défini pour BC, valeur par défaut 0
            'dernieres': self.get_serializer(qs.order_by('-date_creation')[:5], many=True).data,
            'a_traiter': self.get_serializer(
                qs.filter(statut_bc__in=[StatutBC.EN_ATTENTE, StatutBC.EN_TRAITEMENT]).order_by('-date_creation')[:5],
                many=True,
            ).data,
        }
        return Response({'message': 'Statistiques des bons de commande', 'data': data}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['get'], url_path='history')
    def history(self, request, pk=None):
        bc = self.get_object()
        return build_history_response(self, self.audit_type, bc.id)

    @action(detail=True, methods=['post'], url_path='assign-agent')
    def assign_agent(self, request, pk=None):
        agent_id = request.data.get('agent_id') or request.data.get('agent_traitant_id')
        bc = self.get_object()
        if agent_id in [None, '', 'null']:
            bc.agent_traitant = None
            bc.save(update_fields=['agent_traitant'])
            log_audit(
                request.user,
                'bon_commande_assign_agent',
                type_objet=self.audit_type,
                id_objet=bc.id,
                request=request,
                details='Agent traitant retiré',
            )
            serializer = self.get_serializer(bc)
            return Response(
                {'message': 'Agent traitant retiré avec succès', 'data': serializer.data},
                status=status.HTTP_200_OK,
            )

        agent = get_object_or_404(Utilisateur, pk=agent_id)
        bc.agent_traitant = agent
        bc.save(update_fields=['agent_traitant'])
        log_audit(
            request.user,
            'bon_commande_assign_agent',
            type_objet=self.audit_type,
            id_objet=bc.id,
            request=request,
            details=f'Agent traitant défini: {agent.id}',
        )
        serializer = self.get_serializer(bc)
        return Response(
            {'message': 'Agent traitant mis à jour avec succès', 'data': serializer.data},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['post'], url_path='ordre-virement')
    def ordre_virement(self, request, pk=None):
        pourcentage_raw = request.data.get('pourcentage') or request.data.get('pourcentage_paiement')
        if pourcentage_raw in [None, '', 'null']:
            return Response(
                {'message': 'Validation echouee', 'detail': 'Le champ pourcentage est requis.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            pourcentage = Decimal(str(pourcentage_raw))
        except (InvalidOperation, TypeError):
            return Response(
                {'message': 'Validation echouee', 'detail': 'Le champ pourcentage est invalide.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if pourcentage <= 0:
            return Response(
                {'message': 'Validation echouee', 'detail': 'Le pourcentage doit etre superieur a 0.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        banque_id = request.data.get('banque_id') or request.data.get('id_banque')
        if banque_id in [None, '', 'null']:
            return Response(
                {'message': 'Validation echouee', 'detail': 'Le champ banque_id est requis.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        banque = get_object_or_404(Banque, pk=banque_id)

        bc = self.get_object()
        total_autorise, total_paye = _paiement_totaux(bc)
        if total_autorise <= 0:
            return Response(
                {
                    'message': 'Validation echouee',
                    'detail': 'Impossible de calculer le total autorise pour ce bon de commande.',
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        reste = total_autorise - total_paye
        if reste <= 0:
            return Response(
                {
                    'message': 'Validation echouee',
                    'detail': 'Le montant total autorise est deja entierement paye.',
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        montant_calcule = _quantize_money((total_autorise * pourcentage) / Decimal('100'))
        montant_effectif = montant_calcule
        if montant_effectif > reste:
            montant_effectif = _quantize_money(reste)
        if montant_effectif <= 0:
            return Response(
                {
                    'message': 'Validation echouee',
                    'detail': 'Le montant calcule est insuffisant.',
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        facture_id = request.data.get('facture_id') or request.data.get('id_facture')
        facture = None
        if facture_id not in [None, '', 'null']:
            facture = get_object_or_404(Facture, pk=facture_id, id_bc=bc)
        else:
            date_facture = parse_date(request.data.get('date_facture') or '') or timezone.now().date()
            numero_facture = (request.data.get('numero_facture') or '').strip()
            if not numero_facture:
                base = (bc.numero_bc or 'BC').strip().replace(' ', '')
                suffix = timezone.now().strftime('%Y%m%d%H%M%S')
                numero_facture = f'FAC/AUTO/{base}/{suffix}'
                if len(numero_facture) > 100:
                    numero_facture = numero_facture[:100]
            facture = Facture.objects.create(
                id_bc=bc,
                numero_facture=numero_facture,
                id_devise=bc.id_devise,
                montant_ht=montant_effectif,
                montant_ttc=montant_effectif,
                date_facture=date_facture,
                statut_facture=StatutFacture.ATTENTE_PAIEMENT,
            )

        methode_id = request.data.get('methode_paiement_id') or request.data.get('id_methode_paiement')
        if methode_id not in [None, '', 'null']:
            methode = get_object_or_404(MethodePaiement, pk=methode_id)
        else:
            methode = MethodePaiement.objects.filter(code__iexact='VIR').first()
            if methode is None:
                return Response(
                    {
                        'message': 'Validation echouee',
                        'detail': 'Methode de paiement VIR introuvable.',
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        date_ordre = parse_date(request.data.get('date_ordre') or '')
        date_execution = parse_date(request.data.get('date_execution') or '')
        reference_virement = (request.data.get('reference_virement') or '').strip()

        paiement = Paiement.objects.create(
            id_facture=facture,
            id_banque=banque,
            id_methode_paiement=methode,
            montant=montant_effectif,
            date_ordre=date_ordre,
            date_execution=date_execution,
            reference_virement=reference_virement,
            statut_paiement=StatutPaiement.EN_ATTENTE,
            id_tresorier=request.user if getattr(request.user, 'id', None) else None,
        )

        log_audit(
            request.user,
            'bon_commande_ordre_virement',
            type_objet=self.audit_type,
            id_objet=bc.id,
            request=request,
            details=f'Ordre virement {paiement.id} | montant: {montant_effectif}',
        )

        data = {
            'paiement_id': str(paiement.id),
            'montant': str(montant_effectif),
            'pourcentage': str(pourcentage),
            'pourcentage_effectif': str(_quantize_money((montant_effectif / total_autorise) * Decimal('100'))),
            'total_autorise': str(total_autorise),
            'total_paye': str(total_paye),
            'reste': str(total_autorise - total_paye - montant_effectif),
            'total_paye_pourcentage': str(
                _quantize_money((total_paye / total_autorise) * Decimal('100'))
            ),
            'reste_pourcentage': str(
                _quantize_money(((total_autorise - total_paye - montant_effectif) / total_autorise) * Decimal('100'))
            ),
            'date_ordre': paiement.date_ordre,
            'date_execution': paiement.date_execution,
            'date_paiement': paiement.date_execution or paiement.date_ordre,
            'banque': BanqueSerializer(banque).data,
            'facture_id': str(facture.id) if facture else None,
            'facture': (
                {
                    'id': str(facture.id),
                    'numero_facture': facture.numero_facture,
                    'montant_ht': str(facture.montant_ht),
                    'montant_ttc': str(facture.montant_ttc),
                    'date_facture': facture.date_facture,
                    'statut_facture': facture.statut_facture,
                }
                if facture
                else None
            ),
            'methode_paiement': MethodePaiementSerializer(methode).data,
        }
        return Response({'message': 'Ordre de virement genere', 'data': data}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['get'], url_path='paiements')
    def paiements(self, request, pk=None):
        bc = self.get_object()
        total_autorise, total_paye = _paiement_totaux(bc)
        paiements_qs = (
            Paiement.objects.select_related('id_banque', 'id_facture', 'id_methode_paiement')
            .filter(id_facture__id_bc=bc)
            .order_by('-date_ordre', '-date_execution', '-id')
        )
        items = []
        for paiement in paiements_qs:
            pourcentage = None
            if total_autorise > 0:
                pourcentage = _quantize_money((paiement.montant / total_autorise) * Decimal('100'))
            items.append(
                {
                    'id': str(paiement.id),
                    'montant': str(paiement.montant),
                    'date_ordre': paiement.date_ordre,
                    'date_execution': paiement.date_execution,
                    'date_paiement': paiement.date_execution or paiement.date_ordre,
                    'pourcentage': str(pourcentage) if pourcentage is not None else None,
                    'banque': BanqueSerializer(paiement.id_banque).data if paiement.id_banque else None,
                    'fournisseur': FournisseurSerializer(bc.id_fournisseur).data if bc.id_fournisseur else None,
                    'agent_traitant': UserSerializer(bc.agent_traitant).data if bc.agent_traitant else None,
                    'facture_id': str(paiement.id_facture_id) if paiement.id_facture_id else None,
                    'facture': (
                        {
                            'id': str(paiement.id_facture_id),
                            'numero_facture': paiement.id_facture.numero_facture,
                            'montant_ht': str(paiement.id_facture.montant_ht),
                            'montant_ttc': str(paiement.id_facture.montant_ttc),
                            'date_facture': paiement.id_facture.date_facture,
                            'statut_facture': paiement.id_facture.statut_facture,
                        }
                        if paiement.id_facture_id
                        else None
                    ),
                    'statut_paiement': paiement.statut_paiement,
                }
            )
        data = {
            'total_autorise': str(total_autorise),
            'total_paye': str(total_paye),
            'reste': str(total_autorise - total_paye),
            'total_paye_pourcentage': str(
                _quantize_money((total_paye / total_autorise) * Decimal('100'))
            )
            if total_autorise > 0
            else None,
            'reste_pourcentage': str(
                _quantize_money(((total_autorise - total_paye) / total_autorise) * Decimal('100'))
            )
            if total_autorise > 0
            else None,
            'paiements': items,
        }
        return Response({'message': 'Historique des paiements', 'data': data}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'], url_path='ligne-budgetaire')
    def update_ligne_budgetaire(self, request, pk=None):
        valeur = request.data.get('id_ligne_budgetaire') or request.data.get('ligne_budgetaire')
        if valeur in [None, '', 'null']:
            return Response(
                {'message': 'Validation échouée', 'detail': 'Le champ id_ligne_budgetaire est requis.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        bc = self.get_object()
        bc.id_ligne_budgetaire = valeur
        bc.save(update_fields=['id_ligne_budgetaire'])
        log_audit(
            request.user,
            'bon_commande_update_ligne_budgetaire',
            type_objet=self.audit_type,
            id_objet=bc.id,
            request=request,
            details=f'Ligne budgétaire mise à jour: {valeur}',
        )
        serializer = self.get_serializer(bc)
        return Response(
            {'message': 'Ligne budgétaire mise à jour avec succès', 'data': serializer.data},
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=['post'], url_path='transfer')
    def transfer(self, request, pk=None):
        departement_id = request.data.get('departement_id')
        raison = (request.data.get('raison') or '').strip()
        if not departement_id:
            return Response(
                {'message': 'Validation échouée', 'detail': 'Le champ departement_id est requis.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if not raison:
            return Response(
                {'message': 'Validation échouée', 'detail': 'Le champ raison est requis.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        departement = get_object_or_404(Departement, pk=departement_id)
        bc = self.get_object()

        if bc.id_departement_id == departement.id:
            return Response(
                {'message': 'Validation échouée', 'detail': 'Le bon de commande est déjà rattaché à ce département.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        last_transfer = bc.transferts.order_by('-date_transfert').first()
        departement_source = last_transfer.departement_beneficiaire if last_transfer else bc.id_departement
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
                    f'Transfert vers le département {departement.nom}'
                    + (' avec mise à jour de la demande liée' if demande_updated else '')
                    + f' | raison: {raison}'
                ),
            )

        serializer = self.get_serializer(bc)
        return Response(
            {'message': 'Transfert de bon de commande effectué avec succès', 'data': serializer.data},
            status=status.HTTP_200_OK,
        )


class DashboardView(APIView):
    """
    Endpoint de synthèse : métriques et dernières demandes/BC.
    """

    def get(self, request, format=None):
        user = request.user
        demandes_qs = Demande.objects.select_related('id_departement', 'id_fournisseur').prefetch_related('lignes', 'documents')
        bc_qs = BonCommande.objects.select_related(
            'id_demande',
            'id_fournisseur',
            'id_departement',
            'id_methode_paiement',
            'id_devise',
            'id_redacteur',
            'id_demande_valider',
        ).prefetch_related('lignes', 'documents')

        demandes_qs = filter_demandes_for_user(demandes_qs, user)
        bc_qs = filter_bc_for_user(bc_qs, user)

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
                'lignes_demande_total': filter_by_departement(
                    LigneDemande.objects.all(), user, 'id_demande__id_departement_id'
                ).count(),
                'lignes_bc_total': LigneBC.objects.filter(
                    id_bc__in=filter_bc_for_user(BonCommande.objects.all(), user).values('id')
                ).count(),
                'documents_total': filter_by_departement(
                    Document.objects.all(), user, 'id_utilisateur__id_departement_id'
                ).count(),
                'transferts_total': filter_transferts_for_user(Transfert.objects.all(), user).count(),
                'factures_total': filter_by_departement(
                    Facture.objects.all(), user, 'id_bc__id_departement_id'
                ).count(),
                'paiements_total': filter_by_departement(
                    Paiement.objects.all(), user, 'id_facture__id_bc__id_departement_id'
                ).count(),
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
        return Response({'message': 'Dashboard récupéré avec succès', 'data': data}, status=status.HTTP_200_OK)


class LigneBCViewSet(AuditModelViewSet):
    queryset = LigneBC.objects.select_related('id_bc', 'id_article', 'id_devise').all()
    serializer_class = LigneBCSerializer
    audit_prefix = 'ligne_bc'
    audit_type = 'LIGNE_BC'

    def perform_create(self, serializer):
        super().perform_create(serializer)
        instance = serializer.instance
        _update_bc_montant_engage(getattr(instance, 'id_bc', None))

    def perform_update(self, serializer):
        old_bc = getattr(self.get_object(), 'id_bc', None)
        super().perform_update(serializer)
        new_bc = getattr(serializer.instance, 'id_bc', None)
        if old_bc and (not new_bc or old_bc.id != new_bc.id):
            _update_bc_montant_engage(old_bc)
        if new_bc:
            _update_bc_montant_engage(new_bc)

    def perform_destroy(self, instance):
        bc = getattr(instance, 'id_bc', None)
        super().perform_destroy(instance)
        _update_bc_montant_engage(bc)

    def get_queryset(self):
        qs = super().get_queryset()
        bc = self.request.GET.get('bc_id')
        article = self.request.GET.get('article_id')
        if bc:
            qs = qs.filter(id_bc_id=bc)
        if article:
            qs = qs.filter(id_article_id=article)
        return filter_by_departement(qs, self.request.user, 'id_bc__id_departement_id')

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        qs = self.filter_queryset(self.get_queryset())
        data = {
            'total': qs.count(),
            'derniers': self.get_serializer(qs.order_by('-id')[:5], many=True).data,
            'a_traiter': [],
        }
        return Response({'message': 'Statistiques des lignes BC', 'data': data}, status=status.HTTP_200_OK)


class SignatureBCViewSet(AuditModelViewSet):
    queryset = SignatureBC.objects.select_related(
        'id_bc',
        'id_signataire',
        'id_signataire__signature_utilisateur',
        'id_document_preuve',
    ).all()
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

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        qs = self.filter_queryset(self.get_queryset())
        counts = dict(qs.values_list('decision').annotate(total=models.Count('id')))
        data = {
            'total': qs.count(),
            'en_attente': counts.get(DecisionSignature.EN_ATTENTE, 0),
            'approuve': counts.get(DecisionSignature.APPROUVE, 0),
            'refuse': counts.get(DecisionSignature.REFUSE, 0),
            'derniers': self.get_serializer(qs.order_by('-date_signature')[:5], many=True).data,
            'a_traiter': self.get_serializer(qs.filter(decision=DecisionSignature.EN_ATTENTE).order_by('-date_signature')[:5], many=True).data,
        }
        return Response({'message': 'Statistiques des signatures BC', 'data': data}, status=status.HTTP_200_OK)


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
        return filter_by_departement(qs, self.request.user, 'id_bc__id_departement_id')

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        qs = self.filter_queryset(self.get_queryset())
        counts = dict(qs.values_list('statut_facture').annotate(total=models.Count('id')))
        data = {
            'total': qs.count(),
            'recue': counts.get(StatutFacture.RECUE, 0),
            'validee': counts.get(StatutFacture.VALIDEE, 0),
            'attente_paiement': counts.get(StatutFacture.ATTENTE_PAIEMENT, 0),
            'payee': counts.get(StatutFacture.PAYEE, 0),
            'rejete': counts.get(StatutFacture.REJETEE, 0),
            'derniers': self.get_serializer(qs.order_by('-date_facture')[:5], many=True).data,
            'a_traiter': self.get_serializer(
                qs.filter(statut_facture__in=[StatutFacture.RECUE, StatutFacture.ATTENTE_PAIEMENT, StatutFacture.VALIDEE])
                .order_by('-date_facture')[:5],
                many=True,
            ).data,
        }
        return Response({'message': 'Statistiques des factures', 'data': data}, status=status.HTTP_200_OK)


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
        return filter_by_departement(qs, self.request.user, 'id_facture__id_bc__id_departement_id')

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        qs = self.filter_queryset(self.get_queryset())
        counts = dict(qs.values_list('statut_paiement').annotate(total=models.Count('id')))
        data = {
            'total': qs.count(),
            'en_attente': counts.get(StatutPaiement.EN_ATTENTE, 0),
            'en_cours': counts.get(StatutPaiement.EN_COURS, 0),
            'execute': counts.get(StatutPaiement.EXECUTE, 0),
            'rejete': counts.get(StatutPaiement.REJETE, 0),
            'derniers': self.get_serializer(qs.order_by('-date_ordre', '-date_execution')[:5], many=True).data,
            'a_traiter': self.get_serializer(
                qs.filter(statut_paiement__in=[StatutPaiement.EN_ATTENTE, StatutPaiement.EN_COURS])
                .order_by('-date_ordre', '-date_execution')[:5],
                many=True,
            ).data,
        }
        return Response({'message': 'Statistiques des paiements', 'data': data}, status=status.HTTP_200_OK)
