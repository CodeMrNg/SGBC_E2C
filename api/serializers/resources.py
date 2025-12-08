from rest_framework import serializers

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
    TypeArticle,
    Utilisateur,
)
from .organisation import DepartementSerializer
from .auth import UserSerializer


class BaseDepthSerializer(serializers.ModelSerializer):
    class Meta:
        depth = 1
        fields = '__all__'


class DeviseSerializer(BaseDepthSerializer):
    class Meta(BaseDepthSerializer.Meta):
        model = Devise


class MethodePaiementSerializer(BaseDepthSerializer):
    class Meta(BaseDepthSerializer.Meta):
        model = MethodePaiement


class CategorieSerializer(BaseDepthSerializer):
    class Meta(BaseDepthSerializer.Meta):
        model = Categorie


class ArticleSerializer(BaseDepthSerializer):
    type_article = serializers.ChoiceField(
        choices=TypeArticle.choices,
        required=False,
        default=TypeArticle.ARTICLE,
    )

    class Meta(BaseDepthSerializer.Meta):
        model = Article

    def validate(self, attrs):
        """
        Force un type par défaut si absent pour éviter un type_article NULL.
        """
        if 'type_article' not in attrs or not attrs.get('type_article'):
            attrs['type_article'] = TypeArticle.ARTICLE
        return attrs


class FournisseurSerializer(BaseDepthSerializer):
    class Meta(BaseDepthSerializer.Meta):
        model = Fournisseur


class BanqueSerializer(BaseDepthSerializer):
    class Meta(BaseDepthSerializer.Meta):
        model = Banque


class FournisseurRIBSerializer(BaseDepthSerializer):
    class Meta(BaseDepthSerializer.Meta):
        model = FournisseurRIB


class LigneDemandeSerializer(BaseDepthSerializer):
    id_article = ArticleSerializer(read_only=True)
    id_fournisseur = FournisseurSerializer(read_only=True)
    id_devise = DeviseSerializer(read_only=True)
    id_demande_id = serializers.PrimaryKeyRelatedField(
        queryset=Demande.objects.all(),
        source='id_demande',
        write_only=True,
        required=False,
    )
    id_article_id = serializers.PrimaryKeyRelatedField(
        queryset=Article.objects.all(),
        source='id_article',
        write_only=True,
        required=False,
        allow_null=True,
    )
    id_fournisseur_id = serializers.PrimaryKeyRelatedField(
        queryset=Fournisseur.objects.all(),
        source='id_fournisseur',
        write_only=True,
        required=False,
        allow_null=True,
    )
    id_devise_id = serializers.PrimaryKeyRelatedField(
        queryset=Devise.objects.all(),
        source='id_devise',
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta(BaseDepthSerializer.Meta):
        model = LigneDemande

    def validate(self, attrs):
        """
        Autorise l'envoi de id_demande via id_demande_id ou id_demande (compat clients).
        """
        if 'id_demande' not in attrs:
            demande_id = self.initial_data.get('id_demande')
            if demande_id:
                try:
                    attrs['id_demande'] = Demande.objects.get(pk=demande_id)
                except Demande.DoesNotExist:
                    raise serializers.ValidationError({'id_demande': 'Demande introuvable.'})
        if self.instance is None and 'id_demande' not in attrs:
            raise serializers.ValidationError({'id_demande': 'Ce champ est requis.'})

        # Champs optionnels : mapper si présents
        if 'id_article' not in attrs and 'id_article_id' not in self.initial_data:
            article_id = self.initial_data.get('id_article')
            if article_id:
                try:
                    attrs['id_article'] = Article.objects.get(pk=article_id)
                except Article.DoesNotExist:
                    raise serializers.ValidationError({'id_article': 'Article introuvable.'})

        if 'id_fournisseur' not in attrs and 'id_fournisseur_id' not in self.initial_data:
            fournisseur_id = self.initial_data.get('id_fournisseur')
            if fournisseur_id:
                try:
                    attrs['id_fournisseur'] = Fournisseur.objects.get(pk=fournisseur_id)
                except Fournisseur.DoesNotExist:
                    raise serializers.ValidationError({'id_fournisseur': 'Fournisseur introuvable.'})

        if 'id_devise' not in attrs and 'id_devise_id' not in self.initial_data:
            devise_id = self.initial_data.get('id_devise')
            if devise_id:
                try:
                    attrs['id_devise'] = Devise.objects.get(pk=devise_id)
                except Devise.DoesNotExist:
                    raise serializers.ValidationError({'id_devise': 'Devise introuvable.'})
        return attrs


class LigneBudgetaireSerializer(BaseDepthSerializer):
    class Meta(BaseDepthSerializer.Meta):
        model = LigneBudgetaire


class DocumentSerializer(BaseDepthSerializer):
    chemin_fichier = serializers.FileField(allow_empty_file=False)
    id_utilisateur = UserSerializer(read_only=True)
    id_utilisateur_id = serializers.PrimaryKeyRelatedField(
        queryset=Utilisateur.objects.all(),
        source='id_utilisateur',
        write_only=True,
        required=False,
        allow_null=True,
    )
    id_demande = serializers.PrimaryKeyRelatedField(
        queryset=Demande.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )
    id_bc = serializers.PrimaryKeyRelatedField(
        queryset=BonCommande.objects.all(),
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta(BaseDepthSerializer.Meta):
        model = Document

    def validate(self, attrs):
        """
        Autorise id_demande/id_bc ou leurs alias demande_id/bc_id et impose
        qu'au moins l'un des deux soit fourni à la création.
        """
        if 'id_demande' not in attrs:
            demande_id = self.initial_data.get('demande_id') or self.initial_data.get('id_demande')
            if demande_id:
                try:
                    attrs['id_demande'] = Demande.objects.get(pk=demande_id)
                except Demande.DoesNotExist:
                    raise serializers.ValidationError({'id_demande': 'Demande introuvable.'})

        if 'id_bc' not in attrs:
            bc_id = self.initial_data.get('bc_id') or self.initial_data.get('id_bc')
            if bc_id:
                try:
                    attrs['id_bc'] = BonCommande.objects.get(pk=bc_id)
                except BonCommande.DoesNotExist:
                    raise serializers.ValidationError({'id_bc': 'Bon de commande introuvable.'})

        if self.instance is None and not attrs.get('id_demande') and not attrs.get('id_bc'):
            raise serializers.ValidationError({'non_field_errors': 'Fournir id_demande ou id_bc.'})

        return attrs

    def create(self, validated_data):
        demande = validated_data.pop('id_demande', None)
        bc = validated_data.pop('id_bc', None)
        # Always attach the authenticated user when none is provided.
        user = validated_data.pop('id_utilisateur', None) or self.context['request'].user
        if user is None or not getattr(user, 'id', None):
            raise serializers.ValidationError({'id_utilisateur': 'Utilisateur requis.'})
        validated_data['id_utilisateur'] = user
        document = super().create(validated_data)
        if demande:
            document.demandes.add(demande)
        if bc:
            document.bons_commande.add(bc)
        return document

    def update(self, instance, validated_data):
        demande = validated_data.pop('id_demande', None)
        bc = validated_data.pop('id_bc', None)
        document = super().update(instance, validated_data)
        if demande:
            document.demandes.add(demande)
        if bc:
            document.bons_commande.add(bc)
        return document


class SignatureNumeriqueSerializer(BaseDepthSerializer):
    class Meta(BaseDepthSerializer.Meta):
        model = SignatureNumerique


class TransfertLiteSerializer(serializers.ModelSerializer):
    departement_source = DepartementSerializer(read_only=True)
    departement_beneficiaire = DepartementSerializer(read_only=True)
    agent = UserSerializer(read_only=True)

    class Meta:
        model = Transfert
        fields = (
            'id',
            'departement_source',
            'departement_beneficiaire',
            'statut',
            'raison',
            'agent',
            'date_transfert',
        )


class DemandeSerializer(BaseDepthSerializer):
    lignes = LigneDemandeSerializer(many=True, read_only=True)
    documents = DocumentSerializer(many=True, read_only=True)
    id_departement = DepartementSerializer(read_only=True)
    id_departement_id = serializers.PrimaryKeyRelatedField(
        queryset=Departement.objects.all(),
        source='id_departement',
        write_only=True,
        required=False,
    )
    agent_traitant = UserSerializer(read_only=True)
    transferts = TransfertLiteSerializer(many=True, read_only=True)

    class Meta(BaseDepthSerializer.Meta):
        model = Demande
        read_only_fields = ('numero_demande',)

    def validate(self, attrs):
        """
        Permet d'accepter un id_departement passé soit via id_departement_id (champ dédié)
        soit via id_departement (compat Postman/clients existants).
        """
        if 'id_departement' not in attrs:
            departement_id = self.initial_data.get('id_departement')
            if departement_id:
                try:
                    attrs['id_departement'] = Departement.objects.get(pk=departement_id)
                except Departement.DoesNotExist:
                    raise serializers.ValidationError({'id_departement': 'Département introuvable.'})
        if self.instance is None and 'id_departement' not in attrs:
            raise serializers.ValidationError({'id_departement': 'Ce champ est requis.'})
        return attrs


class DemandePrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    def to_representation(self, value):
        return DemandeSerializer(value, context=self.context).data


class DepartementPrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    def to_representation(self, value):
        return DepartementSerializer(value, context=self.context).data


class DevisePrimaryKeyRelatedField(serializers.PrimaryKeyRelatedField):
    def to_representation(self, value):
        return DeviseSerializer(value, context=self.context).data


class LigneBCSerializer(BaseDepthSerializer):
    id_article = ArticleSerializer(read_only=True)
    id_devise = DeviseSerializer(read_only=True)
    id_bc_id = serializers.PrimaryKeyRelatedField(
        queryset=BonCommande.objects.all(),
        source='id_bc',
        write_only=True,
        required=False,
    )
    id_article_id = serializers.PrimaryKeyRelatedField(
        queryset=Article.objects.all(),
        source='id_article',
        write_only=True,
        required=False,
        allow_null=True,
    )
    id_devise_id = serializers.PrimaryKeyRelatedField(
        queryset=Devise.objects.all(),
        source='id_devise',
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta(BaseDepthSerializer.Meta):
        model = LigneBC

    def validate(self, attrs):
        """
        Autorise l'envoi de id_bc via id_bc_id ou id_bc (compat clients).
        """
        if 'id_bc' not in attrs:
            bc_id = self.initial_data.get('id_bc')
            if bc_id:
                try:
                    attrs['id_bc'] = BonCommande.objects.get(pk=bc_id)
                except BonCommande.DoesNotExist:
                    raise serializers.ValidationError({'id_bc': 'Bon de commande introuvable.'})
        if self.instance is None and 'id_bc' not in attrs:
            raise serializers.ValidationError({'id_bc': 'Ce champ est requis.'})

        if 'id_article' not in attrs and 'id_article_id' not in self.initial_data:
            article_id = self.initial_data.get('id_article')
            if article_id:
                try:
                    attrs['id_article'] = Article.objects.get(pk=article_id)
                except Article.DoesNotExist:
                    raise serializers.ValidationError({'id_article': 'Article introuvable.'})

        if 'id_devise' not in attrs and 'id_devise_id' not in self.initial_data:
            devise_id = self.initial_data.get('id_devise')
            if devise_id:
                try:
                    attrs['id_devise'] = Devise.objects.get(pk=devise_id)
                except Devise.DoesNotExist:
                    raise serializers.ValidationError({'id_devise': 'Devise introuvable.'})
        return attrs


class BonCommandeSerializer(BaseDepthSerializer):
    lignes = LigneBCSerializer(many=True, read_only=True)
    documents = DocumentSerializer(many=True, read_only=True)
    id_demande = DemandePrimaryKeyRelatedField(queryset=Demande.objects.all())
    id_fournisseur = FournisseurSerializer(read_only=True)
    id_departement = DepartementPrimaryKeyRelatedField(queryset=Departement.objects.all())
    agent_traitant = UserSerializer(read_only=True)
    id_redacteur = UserSerializer(read_only=True)
    id_redacteur_id = serializers.PrimaryKeyRelatedField(
        queryset=Utilisateur.objects.all(),
        source='id_redacteur',
        write_only=True,
        required=False,
        allow_null=True,
    )
    id_methode_paiement = MethodePaiementSerializer(read_only=True)
    id_devise = DevisePrimaryKeyRelatedField(queryset=Devise.objects.all())
    id_ligne_budgetaire = LigneBudgetaireSerializer(read_only=True)
    transferts = TransfertLiteSerializer(many=True, read_only=True)

    class Meta(BaseDepthSerializer.Meta):
        model = BonCommande
        read_only_fields = ('numero_bc',)

    def to_internal_value(self, data):
        data = dict(data)
        demande_id = data.get('demande_id')
        if demande_id and 'id_demande' not in data:
            data['id_demande'] = demande_id
        departement_id = data.get('departement_id')
        if departement_id and 'id_departement' not in data:
            data['id_departement'] = departement_id
        devise_id = data.get('devise_id')
        if devise_id and 'id_devise' not in data:
            data['id_devise'] = devise_id
        return super().to_internal_value(data)

    def validate(self, attrs):
        """
        Force l'association d'un rédacteur sur création si absent du payload.
        """
        if self.instance is None and 'id_redacteur' not in attrs:
            redacteur_id = self.initial_data.get('id_redacteur') or self.initial_data.get('id_redacteur_id')
            if redacteur_id not in [None, '', 'null']:
                try:
                    attrs['id_redacteur'] = Utilisateur.objects.get(pk=redacteur_id)
                except Utilisateur.DoesNotExist:
                    raise serializers.ValidationError({'id_redacteur': 'Rédacteur introuvable.'})
            else:
                user = getattr(self.context.get('request'), 'user', None)
                if user is None or not getattr(user, 'id', None):
                    raise serializers.ValidationError({'id_redacteur': 'Rédacteur requis.'})
                attrs['id_redacteur'] = user
        return attrs


class SignatureBCSerializer(BaseDepthSerializer):
    class Meta(BaseDepthSerializer.Meta):
        model = SignatureBC


class FactureSerializer(BaseDepthSerializer):
    class Meta(BaseDepthSerializer.Meta):
        model = Facture


class PaiementSerializer(BaseDepthSerializer):
    class Meta(BaseDepthSerializer.Meta):
        model = Paiement


class TransfertSerializer(BaseDepthSerializer):
    departement_source = DepartementSerializer(read_only=True)
    departement_beneficiaire = DepartementSerializer(read_only=True)
    agent = UserSerializer(read_only=True)
    id_demande = DemandeSerializer(read_only=True)
    id_bc = BonCommandeSerializer(read_only=True)

    class Meta(BaseDepthSerializer.Meta):
        model = Transfert
