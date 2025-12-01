from pathlib import Path
from urllib.parse import urljoin

from django.conf import settings
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.forms import UserChangeForm, UserCreationForm
from django.utils.html import format_html

from .models import (
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
    HistoriqueStatut,
    LigneBC,
    LigneBudgetaire,
    LigneDemande,
    MethodePaiement,
    Paiement,
    Permission,
    Role,
    RolePermission,
    SignatureBC,
    SignatureNumerique,
    Transfert,
    TwoFactorCode,
    Utilisateur,
)

IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}


class UtilisateurCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Utilisateur
        fields = (
            'login',
            'email',
            'phone',
            'first_name',
            'last_name',
            'id_departement',
            'id_role',
            'mfa_active',
            'mfa_method',
            'profile_picture',
        )


class UtilisateurChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = Utilisateur
        fields = (
            'login',
            'email',
            'phone',
            'first_name',
            'last_name',
            'id_departement',
            'id_role',
            'mfa_active',
            'mfa_method',
            'profile_picture',
        )


@admin.register(Utilisateur)
class UtilisateurAdmin(UserAdmin):
    add_form = UtilisateurCreationForm
    form = UtilisateurChangeForm
    model = Utilisateur
    list_display = (
        'login',
        'email',
        'first_name',
        'last_name',
        'phone',
        'is_staff',
        'is_active',
        'profile_picture_preview',
    )
    list_display_links = ('login', 'email')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'id_departement', 'id_role')
    search_fields = ('login', 'email', 'first_name', 'last_name', 'phone')
    ordering = ('login',)
    readonly_fields = ('profile_picture_preview',)
    filter_horizontal = ('groups', 'user_permissions')
    fieldsets = (
        (None, {'fields': ('login', 'password')}),
        (
            'Informations personnelles',
            {'fields': ('first_name', 'last_name', 'email', 'phone', 'profile_picture', 'profile_picture_preview')},
        ),
        ('Organisation', {'fields': ('id_departement', 'id_role')}),
        ('Authentification multi-facteur', {'fields': ('mfa_active', 'mfa_method')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Dates importantes', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (
            None,
            {
                'classes': ('wide',),
                'fields': (
                    'login',
                    'email',
                    'phone',
                    'first_name',
                    'last_name',
                    'id_departement',
                    'id_role',
                    'mfa_active',
                    'mfa_method',
                    'profile_picture',
                    'password1',
                    'password2',
                    'is_active',
                    'is_staff',
                    'is_superuser',
                ),
            },
        ),
    )

    @admin.display(description='Photo')
    def profile_picture_preview(self, obj):
        if obj and obj.profile_picture:
            return format_html(
                '<img src="{}" style="height:60px;width:60px;object-fit:cover;border-radius:50%;" />',
                obj.profile_picture.url,
            )
        return '-'


@admin.register(Departement)
class DepartementAdmin(admin.ModelAdmin):
    list_display = ('nom', 'code', 'slug', 'description', 'actif')
    search_fields = ('nom', 'code', 'slug', 'description')
    list_filter = ('actif',)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ('code', 'libelle')
    search_fields = ('code', 'libelle')


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ('code', 'libelle', 'is_active')
    search_fields = ('code', 'libelle')
    list_filter = ('is_active',)


@admin.register(RolePermission)
class RolePermissionAdmin(admin.ModelAdmin):
    list_display = ('id_role', 'id_permission', 'attribue_par', 'date_attribution')
    list_filter = ('id_role', 'id_permission')
    search_fields = ('id_role__libelle', 'id_permission__libelle')


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = (
        'type_document',
        'reference_fonctionnelle',
        'id_utilisateur',
        'statut_archivage',
        'date_generation',
        'file_link',
    )
    search_fields = ('type_document', 'reference_fonctionnelle', 'chemin_fichier')
    list_filter = ('statut_archivage', 'date_generation')
    readonly_fields = ('file_preview', 'date_generation')
    fields = (
        'type_document',
        'reference_fonctionnelle',
        'chemin_fichier',
        'hash_contenu',
        'id_utilisateur',
        'statut_archivage',
        'date_generation',
        'file_preview',
    )

    @staticmethod
    def _build_file_url(document: Document):
        path = (document.chemin_fichier or '').strip()
        if not path:
            return None
        normalized_path = path.replace('\\', '/')
        if normalized_path.startswith(('http://', 'https://', '/')):
            return normalized_path
        return urljoin(settings.MEDIA_URL, normalized_path)

    @admin.display(description='Fichier')
    def file_link(self, obj):
        url = self._build_file_url(obj)
        if not url:
            return '-'
        return format_html('<a href="{}" target="_blank" rel="noopener">Ouvrir</a>', url)

    @admin.display(description='Previsualisation')
    def file_preview(self, obj):
        url = self._build_file_url(obj)
        if not url:
            return '-'
        extension = Path(obj.chemin_fichier).suffix.lower()
        if extension in IMAGE_EXTENSIONS:
            return format_html(
                '<img src="{}" style="max-height:180px;max-width:260px;object-fit:contain;" />',
                url,
            )
        return self.file_link(obj)


@admin.register(SignatureNumerique)
class SignatureNumeriqueAdmin(admin.ModelAdmin):
    list_display = ('id_document', 'id_utilisateur', 'empreinte', 'date_signature')
    search_fields = ('empreinte', 'id_document__reference_fonctionnelle', 'id_utilisateur__login')
    list_filter = ('date_signature',)


@admin.register(Devise)
class DeviseAdmin(admin.ModelAdmin):
    list_display = ('code_iso', 'libelle', 'symbole', 'actif', 'taux_reference', 'date_derniere_maj')
    search_fields = ('code_iso', 'libelle', 'symbole')
    list_filter = ('actif',)


@admin.register(MethodePaiement)
class MethodePaiementAdmin(admin.ModelAdmin):
    list_display = ('code', 'libelle', 'actif')
    search_fields = ('code', 'libelle')
    list_filter = ('actif',)


@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ('code', 'libelle', 'actif')
    search_fields = ('code', 'libelle')
    list_filter = ('actif',)


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    list_display = ('code_article', 'designation', 'id_categorie', 'unite', 'prix_reference', 'id_devise', 'actif')
    search_fields = ('code_article', 'designation')
    list_filter = ('id_categorie', 'actif')


@admin.register(Fournisseur)
class FournisseurAdmin(admin.ModelAdmin):
    list_display = ('code_fournisseur', 'raison_sociale', 'telephone', 'email', 'actif')
    search_fields = ('code_fournisseur', 'raison_sociale', 'telephone', 'email')
    list_filter = ('actif',)


@admin.register(Banque)
class BanqueAdmin(admin.ModelAdmin):
    list_display = ('nom', 'code_banque', 'code_swift', 'actif')
    search_fields = ('nom', 'code_banque', 'code_swift')
    list_filter = ('actif',)


@admin.register(FournisseurRIB)
class FournisseurRIBAdmin(admin.ModelAdmin):
    list_display = (
        'id_fournisseur',
        'id_banque',
        'numero_compte',
        'id_devise',
        'actif',
        'date_creation',
        'date_fin_validite',
    )
    search_fields = ('numero_compte', 'intitule_compte', 'id_fournisseur__raison_sociale')
    list_filter = ('actif', 'id_banque')


@admin.register(Demande)
class DemandeAdmin(admin.ModelAdmin):
    list_display = (
        'numero_demande',
        'objet',
        'source',
        'id_departement',
        'statut_demande',
        'date_creation',
        'date_modification',
        'date_validation_budget',
    )
    search_fields = ('numero_demande', 'objet', 'description', 'source')
    list_filter = ('statut_demande', 'id_departement', 'date_creation', 'date_modification')


@admin.register(LigneDemande)
class LigneDemandeAdmin(admin.ModelAdmin):
    list_display = ('id_demande', 'designation', 'id_article', 'id_fournisseur', 'quantite', 'prix_unitaire_estime')
    search_fields = ('designation', 'id_demande__numero_demande')
    list_filter = ('id_demande', 'id_article')


@admin.register(BonCommande)
class BonCommandeAdmin(admin.ModelAdmin):
    list_display = (
        'numero_bc',
        'id_demande',
        'id_fournisseur',
        'id_departement',
        'statut_bc',
        'date_bc',
        'date_creation',
        'date_modification',
        'echeance',
    )
    search_fields = ('numero_bc',)
    list_filter = ('statut_bc', 'id_departement', 'id_fournisseur', 'date_modification')


@admin.register(LigneBC)
class LigneBCAdmin(admin.ModelAdmin):
    list_display = ('id_bc', 'designation', 'id_article', 'quantite', 'prix_unitaire', 'id_devise', 'prix_net')
    search_fields = ('designation', 'id_bc__numero_bc')
    list_filter = ('id_bc',)


@admin.register(SignatureBC)
class SignatureBCAdmin(admin.ModelAdmin):
    list_display = ('id_bc', 'id_signataire', 'niveau_validation', 'decision', 'date_signature')
    search_fields = ('id_bc__numero_bc', 'id_signataire__login')
    list_filter = ('decision', 'date_signature')


@admin.register(Facture)
class FactureAdmin(admin.ModelAdmin):
    list_display = ('numero_facture', 'id_bc', 'statut_facture', 'montant_ht', 'montant_ttc', 'date_facture')
    search_fields = ('numero_facture', 'id_bc__numero_bc')
    list_filter = ('statut_facture', 'date_facture')


@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = (
        'id_facture',
        'montant',
        'statut_paiement',
        'id_banque',
        'id_methode_paiement',
        'date_ordre',
        'date_execution',
    )
    search_fields = ('id_facture__numero_facture', 'reference_virement')
    list_filter = ('statut_paiement', 'id_banque', 'id_methode_paiement')


@admin.register(LigneBudgetaire)
class LigneBudgetaireAdmin(admin.ModelAdmin):
    list_display = (
        'code_ligne',
        'exercice',
        'id_departement',
        'id_devise',
        'montant_budget',
        'montant_engage',
        'montant_reste',
    )
    search_fields = ('code_ligne', 'chapitre', 'article_budgetaire')
    list_filter = ('exercice', 'id_departement')


@admin.register(Transfert)
class TransfertAdmin(admin.ModelAdmin):
    list_display = (
        'departement_source',
        'departement_beneficiaire',
        'statut',
        'agent',
        'id_demande',
        'id_bc',
        'date_transfert',
    )
    search_fields = (
        'departement_source__nom',
        'departement_beneficiaire__nom',
        'id_demande__numero_demande',
        'id_bc__numero_bc',
        'raison',
    )
    list_filter = ('statut', 'departement_source', 'departement_beneficiaire', 'agent', 'date_transfert')


@admin.register(HistoriqueStatut)
class HistoriqueStatutAdmin(admin.ModelAdmin):
    list_display = ('type_objet', 'id_objet', 'ancien_statut', 'nouveau_statut', 'date_modification', 'id_utilisateur')
    search_fields = ('type_objet', 'ancien_statut', 'nouveau_statut', 'commentaire')
    list_filter = ('type_objet', 'date_modification')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'type_objet', 'id_objet', 'timestamp', 'id_utilisateur', 'ip_client')
    search_fields = ('action', 'type_objet', 'details', 'ip_client')
    list_filter = ('action', 'type_objet', 'timestamp')


@admin.register(TwoFactorCode)
class TwoFactorCodeAdmin(admin.ModelAdmin):
    list_display = ('user', 'method', 'code', 'consumed', 'expires_at', 'created_at', 'updated_at')
    search_fields = ('user__login', 'code')
    list_filter = ('method', 'consumed')
    readonly_fields = ('created_at', 'updated_at')
