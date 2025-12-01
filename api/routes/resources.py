from django.urls import path
from rest_framework.routers import DefaultRouter

from ..views.resources import (
    ArticleViewSet,
    BanqueViewSet,
    BonCommandeViewSet,
    CategorieViewSet,
    DashboardView,
    DemandeViewSet,
    DeviseViewSet,
    DocumentViewSet,
    FactureViewSet,
    FournisseurRIBViewSet,
    FournisseurViewSet,
    LigneBCViewSet,
    LigneBudgetaireViewSet,
    LigneDemandeViewSet,
    MethodePaiementViewSet,
    PaiementViewSet,
    SignatureBCViewSet,
    SignatureNumeriqueViewSet,
    TransfertViewSet,
)

router = DefaultRouter()
router.register(r'devises', DeviseViewSet, basename='devises')
router.register(r'methodes-paiement', MethodePaiementViewSet, basename='methodes-paiement')
router.register(r'categories', CategorieViewSet, basename='categories')
router.register(r'articles', ArticleViewSet, basename='articles')
router.register(r'fournisseurs', FournisseurViewSet, basename='fournisseurs')
router.register(r'banques', BanqueViewSet, basename='banques')
router.register(r'fournisseurs-rib', FournisseurRIBViewSet, basename='fournisseurs-rib')
router.register(r'demandes', DemandeViewSet, basename='demandes')
router.register(r'lignes-demande', LigneDemandeViewSet, basename='lignes-demande')
router.register(r'lignes-budget', LigneBudgetaireViewSet, basename='lignes-budget')
router.register(r'documents', DocumentViewSet, basename='documents')
router.register(r'signatures', SignatureNumeriqueViewSet, basename='signatures')
router.register(r'bons-commande', BonCommandeViewSet, basename='bons-commande')
router.register(r'lignes-bc', LigneBCViewSet, basename='lignes-bc')
router.register(r'signatures-bc', SignatureBCViewSet, basename='signatures-bc')
router.register(r'factures', FactureViewSet, basename='factures')
router.register(r'paiements', PaiementViewSet, basename='paiements')
router.register(r'transferts', TransfertViewSet, basename='transferts')

urlpatterns = router.urls + [
    path('dashboard/', DashboardView.as_view(), name='dashboard'),
]
