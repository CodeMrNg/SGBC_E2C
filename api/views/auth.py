from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.utils import timezone
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from ..auth_utils import (
    generate_tokens_for_user,
    get_user_from_id,
    issue_two_factor_code,
    log_audit,
)
from ..models import TwoFactorCode, TwoFactorMethod
from ..serializers.auth import (
    ChangePasswordSerializer,
    LoginSerializer,
    ResetPasswordConfirmSerializer,
    ResetPasswordSerializer,
    TwoFAEnableSerializer,
    TwoFASendSerializer,
    TwoFAVerifySerializer,
    UserSerializer,
)

User = get_user_model()
password_reset_generator = PasswordResetTokenGenerator()


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        user = User.objects.filter(email__iexact=email).first()
        if not user or not user.check_password(password):
            return Response({'detail': 'Identifiants invalides'}, status=status.HTTP_400_BAD_REQUEST)
        if not user.is_active:
            return Response({'detail': 'Compte inactif'}, status=status.HTTP_403_FORBIDDEN)

        if user.mfa_active:
            try:
                issue_two_factor_code(user, request=request)
            except ValueError as exc:
                return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)
            log_audit(user, 'login_requires_2fa', request=request, details='Mot de passe validé, A2F requise')
            return Response(
                {'detail': 'Code envoyé', 'requires_2fa': True},
                status=status.HTTP_200_OK,
            )

        tokens = generate_tokens_for_user(user)
        log_audit(user, 'login', request=request, details='Authentification réussie')
        return Response(
            {
                **tokens,
                'user': UserSerializer(user).data,
            },
            status=status.HTTP_200_OK,
        )


class RefreshView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        token_str = request.data.get('refresh')
        if not token_str:
            return Response({'detail': 'Refresh token requis'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            submitted_token = RefreshToken(token_str)
        except TokenError:
            return Response({'detail': 'Refresh token invalide'}, status=status.HTTP_401_UNAUTHORIZED)

        user = get_user_from_id(submitted_token.get('user_id'))
        serializer = TokenRefreshSerializer(data={'refresh': token_str})
        try:
            serializer.is_valid(raise_exception=True)
        except InvalidToken as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_401_UNAUTHORIZED)

        data = serializer.validated_data
        if user:
            log_audit(user, 'refresh_token', request=request, details='Renouvellement JWT')
        return Response(data, status=status.HTTP_200_OK)


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        token_str = request.data.get('refresh')
        if not token_str:
            return Response({'detail': 'Refresh token requis'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(token_str)
            token.blacklist()
        except TokenError:
            return Response({'detail': 'Refresh token invalide'}, status=status.HTTP_400_BAD_REQUEST)

        log_audit(request.user, 'logout', request=request, details='Refresh token blacklisté')
        return Response({'detail': 'Déconnecté'}, status=status.HTTP_200_OK)


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data, status=status.HTTP_200_OK)


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not request.user.check_password(serializer.validated_data['old_password']):
            return Response({'detail': 'Ancien mot de passe incorrect'}, status=status.HTTP_400_BAD_REQUEST)

        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save(update_fields=['password'])
        log_audit(request.user, 'change_password', request=request)
        return Response({'detail': 'Mot de passe mis à jour'}, status=status.HTTP_200_OK)


class ResetPasswordView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        user = User.objects.filter(email__iexact=email).first()

        token = None
        if user:
            token = password_reset_generator.make_token(user)
            log_audit(user, 'request_password_reset', request=request, details='Token de réinitialisation généré')
            # Token envoyé par email (backend console)
            user.email_user(
                subject='Réinitialisation de mot de passe',
                message=f'Utilisez ce token pour réinitialiser votre mot de passe: {token}',
            )

        response = {'detail': 'Si un compte existe, un email de réinitialisation a été envoyé.'}
        if settings.DEBUG and token:
            response['token'] = token
        return Response(response, status=status.HTTP_200_OK)


class ResetPasswordConfirmView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ResetPasswordConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        token = serializer.validated_data['token']
        new_password = serializer.validated_data['new_password']

        user = User.objects.filter(email__iexact=email).first()
        if not user:
            return Response({'detail': 'Token invalide'}, status=status.HTTP_400_BAD_REQUEST)

        if not password_reset_generator.check_token(user, token):
            return Response({'detail': 'Token invalide ou expiré'}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save(update_fields=['password'])
        log_audit(user, 'reset_password', request=request, details='Mot de passe réinitialisé')
        return Response({'detail': 'Mot de passe mis à jour'}, status=status.HTTP_200_OK)


class TwoFactorSendView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = TwoFASendSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        method = serializer.validated_data['method']
        try:
            issue_two_factor_code(request.user, method=method, request=request)
        except ValueError as exc:
            return Response({'detail': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        return Response(
            {'detail': f'Code envoyé via {method}'},
            status=status.HTTP_200_OK,
        )


class TwoFactorVerifyView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = TwoFAVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        code = serializer.validated_data['code']

        record = (
            TwoFactorCode.objects.filter(
                code=code,
                consumed=False,
                expires_at__gt=timezone.now(),
            )
            .select_related('user')
            .first()
        )
        if not record:
            return Response({'detail': 'Code invalide ou expiré'}, status=status.HTTP_400_BAD_REQUEST)

        record.consumed = True
        record.save(update_fields=['consumed', 'updated_at'])

        user = record.user
        tokens = generate_tokens_for_user(user)
        log_audit(user, '2fa_verify', request=request, details=f'Méthode: {record.method}')

        return Response(
            {
                **tokens,
                'detail': 'A2F validée',
            },
            status=status.HTTP_200_OK,
        )


class TwoFactorEnableView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = TwoFAEnableSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        method = serializer.validated_data['method']
        request.user.mfa_active = True
        request.user.mfa_method = method
        request.user.save(update_fields=['mfa_active', 'mfa_method'])
        log_audit(request.user, '2fa_enable', request=request, details=f'Méthode: {method}')
        return Response({'detail': f'A2F activée via {method}.'}, status=status.HTTP_200_OK)


class TwoFactorDisableView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        request.user.mfa_active = False
        request.user.save(update_fields=['mfa_active'])
        log_audit(request.user, '2fa_disable', request=request)
        return Response({'detail': 'A2F désactivée.'}, status=status.HTTP_200_OK)
