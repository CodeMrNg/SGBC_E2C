from rest_framework import serializers

from ..models import Departement, SignatureUtilisateur, Utilisateur
from .auth import UserSerializer


class DepartementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Departement
        fields = ['id', 'nom', 'description', 'actif', 'code', 'slug']
        read_only_fields = ('code', 'slug')


class SignatureUtilisateurSerializer(serializers.ModelSerializer):
    utilisateur = UserSerializer(read_only=True)
    utilisateur_id = serializers.PrimaryKeyRelatedField(
        queryset=Utilisateur.objects.all(),
        source='utilisateur',
        write_only=True,
        required=False,
    )

    class Meta:
        model = SignatureUtilisateur
        fields = ['id', 'utilisateur', 'utilisateur_id', 'signature', 'cachet']
