import uuid

from django.db import models


class Categorie(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=50, unique=True)
    libelle = models.CharField(max_length=150)
    actif = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.libelle


class TypeArticle(models.TextChoices):
    ARTICLE = ('article', 'Article')
    SERVICE = ('service', 'Service')


class Article(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code_article = models.CharField(max_length=100, unique=True)
    designation = models.CharField(max_length=255)
    id_categorie = models.ForeignKey(
        'Categorie',
        on_delete=models.PROTECT,
        related_name='articles',
        null=True,
        blank=True,
    )
    type_article = models.CharField(
        max_length=20,
        choices=TypeArticle.choices,
        default=TypeArticle.ARTICLE,
    )
    unite = models.CharField(max_length=50)
    prix_reference = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        null=True,
        blank=True,
    )
    id_devise = models.ForeignKey(
        'Devise',
        on_delete=models.PROTECT,
        related_name='articles',
        null=True,
        blank=True,
    )
    actif = models.BooleanField(default=True)

    def __str__(self) -> str:
        return f'{self.code_article} - {self.designation}'


class Fournisseur(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code_fournisseur = models.CharField(max_length=100, unique=True)
    raison_sociale = models.CharField(max_length=255)
    adresse = models.TextField(blank=True)
    telephone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    description = models.TextField(blank=True)
    actif = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.raison_sociale


class Banque(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    nom = models.CharField(max_length=255)
    code_banque = models.CharField(max_length=50, unique=True)
    code_swift = models.CharField(max_length=50, blank=True)
    adresse = models.TextField(blank=True)
    actif = models.BooleanField(default=True)

    def __str__(self) -> str:
        return self.nom


class FournisseurRIB(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    id_fournisseur = models.ForeignKey(
        'Fournisseur',
        on_delete=models.PROTECT,
        related_name='ribs',
    )
    id_banque = models.ForeignKey(
        'Banque',
        on_delete=models.PROTECT,
        related_name='comptes_fournisseurs',
    )
    intitule_compte = models.CharField(max_length=255)
    numero_compte = models.CharField(max_length=100)
    code_banque = models.CharField(max_length=50, blank=True)
    code_agence = models.CharField(max_length=50, blank=True)
    cle_rib = models.CharField(max_length=10, blank=True)
    id_devise = models.ForeignKey(
        'Devise',
        on_delete=models.PROTECT,
        related_name='ribs',
        null=True,
        blank=True,
    )
    actif = models.BooleanField(default=True)
    date_creation = models.DateField(auto_now_add=True)
    date_fin_validite = models.DateField(null=True, blank=True)

    def __str__(self) -> str:
        return f'{self.id_fournisseur} - {self.numero_compte}'
