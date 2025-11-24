import secrets
from datetime import timedelta
from typing import Optional

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from .models import AuditLog, TwoFactorCode, TwoFactorMethod


def get_client_ip(request) -> Optional[str]:
    if request is None:
        return None
    forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if forwarded_for:
        return forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def log_audit(user, action: str, *, type_objet: str = 'auth', id_objet=None, request=None, details: str = '') -> None:
    AuditLog.objects.create(
        id_utilisateur=user if getattr(user, 'is_authenticated', False) else None,
        action=action,
        type_objet=type_objet,
        id_objet=id_objet,
        ip_client=get_client_ip(request),
        details=details,
    )


def generate_tokens_for_user(user) -> dict:
    refresh = RefreshToken.for_user(user)
    return {
        'access': str(refresh.access_token),
        'refresh': str(refresh),
    }


def _dispatch_two_factor_code(user, code: str, method: str) -> None:
    subject = 'Votre code de vérification'
    message = f'Code A2F : {code}'
    if method in (TwoFactorMethod.EMAIL, TwoFactorMethod.BOTH):
        send_mail(
            subject,
            message,
            getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@example.com'),
            [user.email],
            fail_silently=True,
        )
    phone = getattr(user, 'phone', None)
    if method in (TwoFactorMethod.SMS, TwoFactorMethod.BOTH) and phone:
        _send_sms(phone, message)


def _send_sms(phone: str, message: str) -> None:
    backend = getattr(settings, 'SMS_BACKEND', 'console')
    sender = getattr(settings, 'SMS_SENDER_ID', 'SGBC')

    if backend == 'console' or not backend:
        print(f'[SMS][{sender}] {phone}: {message}')
        return

    # Hook for future HTTP/SMS gateway integration
    if backend == 'custom':
        # Implement your provider call here (e.g., requests.post to SMS_API_URL)
        api_url = getattr(settings, 'SMS_API_URL', '')
        api_key = getattr(settings, 'SMS_API_KEY', '')
        if not api_url or not api_key:
            raise ValueError('SMS_API_URL et SMS_API_KEY doivent être configurés pour le backend custom.')
        # Minimal placeholder for custom integration:
        print(f'[SMS custom] vers {phone} via {api_url} (sender={sender}) : {message}')
        return

    raise ValueError(f'Backend SMS inconnu: {backend}')


def issue_two_factor_code(user, *, method: Optional[str] = None, ttl_minutes: int = 5, request=None) -> TwoFactorCode:
    selected_method = method or user.mfa_method or TwoFactorMethod.EMAIL
    phone = getattr(user, 'phone', None)
    if selected_method == TwoFactorMethod.SMS and not phone:
        raise ValueError('Aucun numéro de téléphone disponible pour SMS.')

    now = timezone.now()
    TwoFactorCode.objects.filter(
        user=user,
        consumed=False,
        expires_at__gt=now,
    ).update(consumed=True)

    code = f'{secrets.randbelow(1_000_000):06d}'
    expires_at = now + timedelta(minutes=ttl_minutes)
    record = TwoFactorCode.objects.create(
        user=user,
        code=code,
        method=selected_method,
        expires_at=expires_at,
    )
    _dispatch_two_factor_code(user, code, selected_method)
    log_audit(user, 'send_2fa_code', request=request, details=f'Méthode: {selected_method}')
    return record


def get_user_from_id(user_id):
    User = get_user_model()
    try:
        return User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return None
