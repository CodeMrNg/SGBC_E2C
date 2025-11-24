from django.contrib.auth import get_user_model, password_validation
from rest_framework import serializers

from ..models import TwoFactorMethod


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
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
        ]


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
