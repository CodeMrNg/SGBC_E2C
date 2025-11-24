import csv
from datetime import datetime, time

from django.http import HttpResponse
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import AuditLog
from ..serializers import AuditLogSerializer


def _apply_filters(queryset, request):
    user_id = request.GET.get('user_id')
    type_objet = request.GET.get('type_objet')
    action = request.GET.get('action')
    id_objet = request.GET.get('id_objet')
    date_min = request.GET.get('date_min')
    date_max = request.GET.get('date_max')

    if user_id:
        queryset = queryset.filter(id_utilisateur_id=user_id)
    if type_objet:
        queryset = queryset.filter(type_objet=type_objet)
    if action:
        queryset = queryset.filter(action=action)
    if id_objet:
        queryset = queryset.filter(id_objet=id_objet)

    if date_min:
        dt = parse_datetime(date_min) or (
            parse_date(date_min) and datetime.combine(parse_date(date_min), time.min)
        )
        if dt:
            queryset = queryset.filter(timestamp__gte=timezone.make_aware(dt) if timezone.is_naive(dt) else dt)

    if date_max:
        dt = parse_datetime(date_max) or (
            parse_date(date_max) and datetime.combine(parse_date(date_max), time.max)
        )
        if dt:
            queryset = queryset.filter(timestamp__lte=timezone.make_aware(dt) if timezone.is_naive(dt) else dt)

    return queryset


class AuditLogListView(generics.ListAPIView):
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        base = AuditLog.objects.select_related('id_utilisateur').order_by('-timestamp')
        return _apply_filters(base, self.request)


class AuditLogDetailView(generics.RetrieveAPIView):
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = AuditLog.objects.select_related('id_utilisateur')
    lookup_field = 'id'
    lookup_url_kwarg = 'pk'


class AuditObjectHistoryView(generics.ListAPIView):
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        base = AuditLog.objects.select_related('id_utilisateur').filter(
            type_objet=self.kwargs['type_objet'],
            id_objet=self.kwargs['id_objet'],
        ).order_by('-timestamp')
        return base


class AuditLogExportView(APIView):
    permission_classes = [permissions.IsAdminUser]

    def get(self, request):
        format_param = request.GET.get('format', 'csv').lower()
        qs = _apply_filters(AuditLog.objects.select_related('id_utilisateur').order_by('-timestamp'), request)

        if format_param == 'json':
            serializer = AuditLogSerializer(qs, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)

        if format_param != 'csv':
            return Response({'detail': "Format supportés: csv, json"}, status=status.HTTP_400_BAD_REQUEST)

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="audit_logs.csv"'
        writer = csv.writer(response)
        writer.writerow(['id', 'action', 'type_objet', 'id_objet', 'timestamp', 'user_login', 'user_email', 'ip_client', 'details'])

        for log in qs:
            writer.writerow([
                log.id,
                log.action,
                log.type_objet,
                log.id_objet,
                log.timestamp.isoformat(),
                getattr(log.id_utilisateur, 'login', ''),
                getattr(log.id_utilisateur, 'email', ''),
                log.ip_client or '',
                log.details.replace('\n', ' ') if log.details else '',
            ])

        return response
