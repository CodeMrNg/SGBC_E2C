import uuid

from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models

from .base import BaseModel
from .security import TwoFactorMethod


class Departement(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    actif = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.nom


class Role(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=20, unique=True)
    libelle = models.CharField(max_length=150)
    description = models.TextField(blank=True)

    def __str__(self) -> str:
        return self.libelle


class Permission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    libelle = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.code


class RolePermission(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id_role = models.ForeignKey(
        'Role',
        on_delete=models.PROTECT,
        related_name='permissions',
    )
    id_permission = models.ForeignKey(
        'Permission',
        on_delete=models.PROTECT,
        related_name='roles',
    )
    date_attribution = models.DateTimeField(null=True, blank=True)
    attribue_par = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='permissions_attribuees',
        null=True,
        blank=True,
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['id_role', 'id_permission'], name='unique_role_permission'),
        ]

    def __str__(self) -> str:
        return f'{self.id_role} -> {self.id_permission}'


class UtilisateurManager(BaseUserManager):
    def create_user(self, login, email, password=None, **extra_fields):
        if not login:
            raise ValueError('Le champ login est requis')
        if not email:
            raise ValueError('Le champ email est requis')
        email = self.normalize_email(email)
        user = self.model(login=login, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, login, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Le superuser doit avoir is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Le superuser doit avoir is_superuser=True')

        return self.create_user(login, email, password, **extra_fields)


class Utilisateur(AbstractUser, BaseModel):
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20, unique=True)
    username = None
    login = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)
    mfa_active = models.BooleanField(default=False)
    mfa_method = models.CharField(
        max_length=10,
        choices=TwoFactorMethod.choices,
        default=TwoFactorMethod.EMAIL,
    )
    id_departement = models.ForeignKey(
        'Departement',
        on_delete=models.PROTECT,
        related_name='utilisateurs',
        null=True,
        blank=True,
    )
    id_role = models.ForeignKey(
        'Role',
        on_delete=models.PROTECT,
        related_name='utilisateurs',
        null=True,
        blank=True,
    )

    USERNAME_FIELD = 'login'
    REQUIRED_FIELDS = ['email', 'phone']
    objects = UtilisateurManager()

    class Meta:
        verbose_name = 'utilisateur'
        verbose_name_plural = 'utilisateurs'

    @property
    def nom(self) -> str:
        return self.last_name

    @nom.setter
    def nom(self, value: str) -> None:
        self.last_name = value

    @property
    def prenom(self) -> str:
        return self.first_name

    @prenom.setter
    def prenom(self, value: str) -> None:
        self.first_name = value

    @property
    def actif(self) -> bool:
        return self.is_active

    @actif.setter
    def actif(self, value: bool) -> None:
        self.is_active = value

    @property
    def dernier_login(self):
        return self.last_login

    @dernier_login.setter
    def dernier_login(self, value) -> None:
        self.last_login = value

    def __str__(self) -> str:
        full_name = self.get_full_name().strip()
        return full_name or self.login
