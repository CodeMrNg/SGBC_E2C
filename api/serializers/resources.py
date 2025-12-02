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
    transferts = TransfertLiteSerializer(many=True, read_only=True)

    class Meta(BaseDepthSerializer.Meta):
        model = Demande


class LigneBCSerializer(BaseDepthSerializer):
    class Meta(BaseDepthSerializer.Meta):
        model = LigneBC


class BonCommandeSerializer(BaseDepthSerializer):
    lignes = LigneBCSerializer(many=True, read_only=True)
    documents = DocumentSerializer(many=True, read_only=True)
    id_demande = DemandeSerializer(read_only=True)
    id_fournisseur = FournisseurSerializer(read_only=True)
    id_departement = DepartementSerializer(read_only=True)
    id_methode_paiement = MethodePaiementSerializer(read_only=True)
    id_devise = DeviseSerializer(read_only=True)
    id_ligne_budgetaire = LigneBudgetaireSerializer(read_only=True)
    transferts = TransfertLiteSerializer(many=True, read_only=True)

    class Meta(BaseDepthSerializer.Meta):
        model = BonCommande
        read_only_fields = ('numero_bc',)


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
