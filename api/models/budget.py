import uuid

from django.db import models


class LigneBudgetaire(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    exercice = models.PositiveIntegerField()
    chapitre = models.CharField(max_length=50)
    article_budgetaire = models.CharField(max_length=50)
    paragraphe = models.CharField(max_length=50, blank=True)
    code_ligne = models.CharField(max_length=100, unique=True)
    id_departement = models.ForeignKey(
        'Departement',
        on_delete=models.PROTECT,
        related_name='lignes_budgetaires',
    )
    id_devise = models.ForeignKey(
        'Devise',
        on_delete=models.PROTECT,
        related_name='lignes_budgetaires',
    )
    montant_budget = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=0,
    )
    montant_engage = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=0,
    )
    montant_reste = models.DecimalField(
        max_digits=18,
        decimal_places=2,
        default=0,
    )

    def __str__(self) -> str:
        return self.code_ligne
