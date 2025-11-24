"""
Serializers regroupés par domaine fonctionnel.
"""

from .auth import (  # noqa: F401
    ChangePasswordSerializer,
    LoginSerializer,
    ResetPasswordConfirmSerializer,
    ResetPasswordSerializer,
    TwoFAEnableSerializer,
    TwoFASendSerializer,
    TwoFAVerifySerializer,
    UserSerializer,
)
from .audit import AuditLogSerializer  # noqa: F401
from .organisation import DepartementSerializer  # noqa: F401
