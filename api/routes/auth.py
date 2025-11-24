from django.urls import path

from ..views.auth import (
    ChangePasswordView,
    LoginView,
    LogoutView,
    MeView,
    RefreshView,
    ResetPasswordConfirmView,
    ResetPasswordView,
    TwoFactorDisableView,
    TwoFactorEnableView,
    TwoFactorSendView,
    TwoFactorVerifyView,
)

urlpatterns = [
    path('login/', LoginView.as_view(), name='auth-login'),
    path('refresh/', RefreshView.as_view(), name='auth-refresh'),
    path('logout/', LogoutView.as_view(), name='auth-logout'),
    path('me/', MeView.as_view(), name='auth-me'),
    path('change-password/', ChangePasswordView.as_view(), name='auth-change-password'),
    path('reset-password/', ResetPasswordView.as_view(), name='auth-reset-password'),
    path('reset-password/confirm/', ResetPasswordConfirmView.as_view(), name='auth-reset-password-confirm'),
    path('2fa/send/', TwoFactorSendView.as_view(), name='auth-2fa-send'),
    path('2fa/verify/', TwoFactorVerifyView.as_view(), name='auth-2fa-verify'),
    path('2fa/enable/', TwoFactorEnableView.as_view(), name='auth-2fa-enable'),
    path('2fa/disable/', TwoFactorDisableView.as_view(), name='auth-2fa-disable'),
]
