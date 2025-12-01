from rest_framework import serializers

from ..models import (
    Article,
    AuditLog,
    BonCommande,
    Demande,
    Departement,
    Document,
    Facture,
    Fournisseur,
    LigneBC,
    LigneDemande,
    MethodePaiement,
    Paiement,
    SignatureBC,
    SignatureNumerique,
    Transfert,
)


class AuditLogSerializer(serializers.ModelSerializer):
    utilisateur_login = serializers.SerializerMethodField()
    utilisateur_email = serializers.SerializerMethodField()
    utilisateur_full_name = serializers.SerializerMethodField()
    utilisateur_role = serializers.SerializerMethodField()
    utilisateur_departement = serializers.SerializerMethodField()
    objet = serializers.SerializerMethodField()
    utilisateur = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = [
            'id',
            'action',
            'type_objet',
            'id_objet',
            'timestamp',
            'ip_client',
            'details',
            'id_utilisateur',
            'utilisateur_login',
            'utilisateur_email',
            'utilisateur_full_name',
            'utilisateur_role',
            'utilisateur_departement',
            'objet',
            'utilisateur',
        ]
        read_only_fields = fields

    def get_utilisateur_login(self, obj):
        user = obj.id_utilisateur
        return getattr(user, 'login', None) if user else None

    def get_utilisateur_email(self, obj):
        user = obj.id_utilisateur
        return getattr(user, 'email', None) if user else None

    def get_utilisateur_full_name(self, obj):
        user = obj.id_utilisateur
        if not user:
            return None
        full = user.get_full_name().strip()
        return full or user.login

    def get_utilisateur_role(self, obj):
        user = obj.id_utilisateur
        return getattr(getattr(user, 'id_role', None), 'code', None) if user else None

    def get_utilisateur_departement(self, obj):
        user = obj.id_utilisateur
        return getattr(getattr(user, 'id_departement', None), 'nom', None) if user else None

    def get_objet(self, obj):
        """
        Retourne des informations minimales sur l'objet audité (id, label).
        """
        mapping = {
            'DEMANDE': Demande,
            'BON_COMMANDE': BonCommande,
            'ARTICLE': Article,
            'DOCUMENT': Document,
            'FACTURE': Facture,
            'PAIEMENT': Paiement,
            'FOURNISSEUR': Fournisseur,
            'LIGNE_DEMANDE': LigneDemande,
            'LIGNE_BC': LigneBC,
            'SIGNATURE_BC': SignatureBC,
            'SIGNATURE_NUMERIQUE': SignatureNumerique,
            'TRANSFERT': Transfert,
            'DEPARTEMENT': Departement,
            'METHODE_PAIEMENT': MethodePaiement,
        }
        model = mapping.get((obj.type_objet or '').upper())
        if not model or not obj.id_objet:
            return None
        instance = model.objects.filter(pk=obj.id_objet).first()
        if not instance:
            return None
        return {
            'id': str(instance.id),
            'label': str(instance),
        }

    def get_utilisateur(self, obj):
        user = obj.id_utilisateur
        if not user:
            return None
        return {
            'id': str(user.id),
            'login': user.login,
            'email': user.email,
            'nom': user.last_name,
            'prenom': user.first_name,
            'role': getattr(getattr(user, 'id_role', None), 'code', None),
            'departement': getattr(getattr(user, 'id_departement', None), 'nom', None),
        }
