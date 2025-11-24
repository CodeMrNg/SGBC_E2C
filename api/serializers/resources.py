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
)


class DeviseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Devise
        fields = '__all__'


class MethodePaiementSerializer(serializers.ModelSerializer):
    class Meta:
        model = MethodePaiement
        fields = '__all__'


class CategorieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Categorie
        fields = '__all__'


class ArticleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Article
        fields = '__all__'


class FournisseurSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fournisseur
        fields = '__all__'


class BanqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Banque
        fields = '__all__'


class FournisseurRIBSerializer(serializers.ModelSerializer):
    class Meta:
        model = FournisseurRIB
        fields = '__all__'


class DemandeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Demande
        fields = '__all__'


class LigneDemandeSerializer(serializers.ModelSerializer):
    class Meta:
        model = LigneDemande
        fields = '__all__'


class LigneBudgetaireSerializer(serializers.ModelSerializer):
    class Meta:
        model = LigneBudgetaire
        fields = '__all__'


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = '__all__'


class SignatureNumeriqueSerializer(serializers.ModelSerializer):
    class Meta:
        model = SignatureNumerique
        fields = '__all__'


class BonCommandeSerializer(serializers.ModelSerializer):
    class Meta:
        model = BonCommande
        fields = '__all__'


class LigneBCSerializer(serializers.ModelSerializer):
    class Meta:
        model = LigneBC
        fields = '__all__'


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
