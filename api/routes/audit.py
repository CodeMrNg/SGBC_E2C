from django.urls import path

from ..views.audit import (
    AuditLogDetailView,
    AuditLogExportView,
    AuditLogListView,
    AuditObjectHistoryView,
)

urlpatterns = [
    path('logs/', AuditLogListView.as_view(), name='audit-logs'),
    path('logs/<uuid:pk>/', AuditLogDetailView.as_view(), name='audit-log-detail'),
    path('object/<str:type_objet>/<uuid:id_objet>/', AuditObjectHistoryView.as_view(), name='audit-object-history'),
    path('logs/export/', AuditLogExportView.as_view(), name='audit-logs-export'),
]
