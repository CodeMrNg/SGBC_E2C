from rest_framework import serializers

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
    Transfert,
)


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
    class Meta(BaseDepthSerializer.Meta):
        model = Article


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
    class Meta(BaseDepthSerializer.Meta):
        model = LigneDemande


class LigneBudgetaireSerializer(BaseDepthSerializer):
    class Meta(BaseDepthSerializer.Meta):
        model = LigneBudgetaire


class DocumentSerializer(BaseDepthSerializer):
    class Meta(BaseDepthSerializer.Meta):
        model = Document


class SignatureNumeriqueSerializer(BaseDepthSerializer):
    class Meta(BaseDepthSerializer.Meta):
        model = SignatureNumerique


class DemandeSerializer(BaseDepthSerializer):
    lignes = LigneDemandeSerializer(many=True, read_only=True)
    documents = DocumentSerializer(many=True, read_only=True)

    class Meta(BaseDepthSerializer.Meta):
        model = Demande


class LigneBCSerializer(serializers.ModelSerializer):
    class Meta:
        model = LigneBC
        fields = '__all__'


class BonCommandeSerializer(BaseDepthSerializer):
    lignes = LigneBCSerializer(many=True, read_only=True)
    documents = DocumentSerializer(many=True, read_only=True)

    class Meta(BaseDepthSerializer.Meta):
        model = BonCommande
        read_only_fields = ('numero_bc',)


class SignatureBCSerializer(serializers.ModelSerializer):
    class Meta:
        model = SignatureBC
        fields = '__all__'


class FactureSerializer(serializers.ModelSerializer):
    class Meta:
        model = Facture
        fields = '__all__'


class PaiementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Paiement
        fields = '__all__'


class TransfertSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transfert
        fields = '__all__'
