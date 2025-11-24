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
from .role import RoleSerializer  # noqa: F401
from .resources import (  # noqa: F401
    ArticleSerializer,
    BanqueSerializer,
    BonCommandeSerializer,
    CategorieSerializer,
    DemandeSerializer,
    DeviseSerializer,
    DocumentSerializer,
    FactureSerializer,
    FournisseurRIBSerializer,
    FournisseurSerializer,
    LigneBCSerializer,
    LigneBudgetaireSerializer,
    LigneDemandeSerializer,
    MethodePaiementSerializer,
    PaiementSerializer,
    SignatureBCSerializer,
    SignatureNumeriqueSerializer,
)
