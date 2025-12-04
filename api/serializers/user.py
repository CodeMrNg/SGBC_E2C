from django.contrib.auth import get_user_model, password_validation
from rest_framework import serializers

from .auth import UserSerializer

User = get_user_model()


class UserManagementSerializer(UserSerializer):
    """
    Serializer dédié à la gestion des utilisateurs (création/mise à jour).
    Inclut les relations, l'état actif et le mot de passe en écriture.
    """

    password = serializers.CharField(write_only=True, required=False)
    actif = serializers.BooleanField(source='is_active', required=False)

    class Meta(UserSerializer.Meta):
        model = User
        fields = UserSerializer.Meta.fields + [
            'id_departement',
            'id_role',
            'peut_rediger',
            'peut_signer',
            'actif',
            'password',
        ]
        extra_kwargs = {
            'password': {'write_only': True, 'required': False},
            'id_departement': {'required': False, 'allow_null': True},
            'id_role': {'required': False, 'allow_null': True},
            'actif': {'required': False},
            'peut_rediger': {'required': False},
            'peut_signer': {'required': False},
        }

    def validate_email(self, value):
        qs = User.objects.filter(email__iexact=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('Cet email est déjà utilisé.')
        return value

    def validate_phone(self, value):
        qs = User.objects.filter(phone=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError('Ce numéro est déjà utilisé.')
        return value

    def validate_password(self, value):
        if value:
            password_validation.validate_password(value)
        return value

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        if not password:
            raise serializers.ValidationError({'password': 'Mot de passe requis.'})
        user = User.objects.create_user(password=password, **validated_data)
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save(update_fields=['password', 'updated_at'])
        return user
