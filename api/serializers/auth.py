from django.contrib.auth import get_user_model, password_validation
from rest_framework import serializers

from ..models import TwoFactorMethod


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    departement = serializers.SerializerMethodField()
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id',
            'login',
            'email',
            'first_name',
            'last_name',
            'phone',
            'profile_picture',
            'mfa_active',
            'mfa_method',
            'peut_rediger',
            'peut_signer',
            'departement',
            'role',
        ]

    def get_departement(self, obj):
        dept = getattr(obj, 'id_departement', None)
        if not dept:
            return None
        return {'id': str(dept.id), 'nom': dept.nom}

    def get_role(self, obj):
        role = getattr(obj, 'id_role', None)
        if not role:
            return None
        return {'id': str(role.id), 'libelle': role.libelle, 'code': role.code}


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'profile_picture']
        extra_kwargs = {
            'email': {'required': False},
            'phone': {'required': False},
        }

    def validate_email(self, value):
        user = self.instance
        if value and User.objects.exclude(pk=user.pk).filter(email__iexact=value).exists():
            raise serializers.ValidationError('Cet email est déjà utilisé.')
        return value

    def validate_phone(self, value):
        user = self.instance
        if value and User.objects.exclude(pk=user.pk).filter(phone=value).exists():
            raise serializers.ValidationError('Ce numéro est déjà utilisé.')
        return value


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        password_validation.validate_password(value)
        return value


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetPasswordConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    token = serializers.CharField()
    new_password = serializers.CharField(write_only=True)

    def validate_new_password(self, value):
        password_validation.validate_password(value)
        return value


class TwoFASendSerializer(serializers.Serializer):
    method = serializers.ChoiceField(
        choices=TwoFactorMethod.choices,
        default=TwoFactorMethod.EMAIL,
    )


class TwoFAVerifySerializer(serializers.Serializer):
    code = serializers.CharField(max_length=6)


class TwoFAEnableSerializer(serializers.Serializer):
    method = serializers.ChoiceField(choices=TwoFactorMethod.choices)
