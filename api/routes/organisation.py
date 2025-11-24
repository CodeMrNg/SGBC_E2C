from django.urls import path

from ..views.organisation import DepartementDetailView, DepartementListCreateView

urlpatterns = [
    path('departements/', DepartementListCreateView.as_view(), name='departement-list-create'),
    path('departements/<uuid:pk>/', DepartementDetailView.as_view(), name='departement-detail'),
]
