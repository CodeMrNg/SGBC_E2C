from django.urls import path

from ..views.organisation import DepartementDetailView, DepartementListCreateView, SignatureUtilisateurView

urlpatterns = [
    path('departements/', DepartementListCreateView.as_view(), name='departement-list-create'),
    path('departements/<uuid:pk>/', DepartementDetailView.as_view(), name='departement-detail'),
    path('utilisateurs/<uuid:user_id>/signature/', SignatureUtilisateurView.as_view(), name='signature-utilisateur'),
]
