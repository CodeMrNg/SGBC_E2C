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
    id_demande_id = serializers.PrimaryKeyRelatedField(
        queryset=Demande.objects.all(),
        source='id_demande',
        write_only=True,
        required=False,
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
        return attrs


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


class LigneBCSerializer(BaseDepthSerializer):
    id_bc_id = serializers.PrimaryKeyRelatedField(
        queryset=BonCommande.objects.all(),
        source='id_bc',
        write_only=True,
        required=False,
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
        return attrs


class BonCommandeSerializer(BaseDepthSerializer):
    lignes = LigneBCSerializer(many=True, read_only=True)
    documents = DocumentSerializer(many=True, read_only=True)
    id_demande = DemandeSerializer(read_only=True)
    id_fournisseur = FournisseurSerializer(read_only=True)
    id_departement = DepartementSerializer(read_only=True)
    agent_traitant = UserSerializer(read_only=True)
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
