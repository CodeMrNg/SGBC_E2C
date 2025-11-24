from django.urls import path

from ..views.role import RoleDetailView, RoleListCreateView

urlpatterns = [
    path('roles/', RoleListCreateView.as_view(), name='role-list-create'),
    path('roles/<uuid:pk>/', RoleDetailView.as_view(), name='role-detail'),
]
