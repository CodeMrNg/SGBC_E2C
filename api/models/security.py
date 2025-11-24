from django.conf import settings
from django.db import models
from django.utils import timezone

from .base import BaseModel


class TwoFactorMethod(models.TextChoices):
    SMS = ('sms', 'SMS')
    EMAIL = ('email', 'Email')
    BOTH = ('both', 'SMS et Email')


class TwoFactorCode(BaseModel):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='two_factor_codes',
    )
    code = models.CharField(max_length=6)
    method = models.CharField(
        max_length=10,
        choices=TwoFactorMethod.choices,
        default=TwoFactorMethod.EMAIL,
    )
    expires_at = models.DateTimeField()
    consumed = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def is_valid(self) -> bool:
        return not self.consumed and self.expires_at > timezone.now()

    def __str__(self) -> str:
        return f'2FA {self.method} - {self.code}'
