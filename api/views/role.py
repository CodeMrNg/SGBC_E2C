from django.db.models import Q
from rest_framework import generics, permissions

from ..auth_utils import log_audit
from ..models import Role
from ..serializers.role import RoleSerializer


class RoleListCreateView(generics.ListCreateAPIView):
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Role.objects.all()
        code = self.request.GET.get('code')
        search = self.request.GET.get('search')
        if code:
            qs = qs.filter(code__icontains=code)
        if search:
            qs = qs.filter(Q(code__icontains=search) | Q(libelle__icontains=search) | Q(description__icontains=search))
        return qs.order_by('code')

    def perform_create(self, serializer):
        instance = serializer.save()
        log_audit(self.request.user, 'role_create', type_objet='ROLE', id_objet=instance.id, request=self.request)


class RoleDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'
    lookup_url_kwarg = 'pk'

    def get_queryset(self):
        return Role.objects.order_by('code')

    def perform_update(self, serializer):
        instance = serializer.save()
        log_audit(self.request.user, 'role_update', type_objet='ROLE', id_objet=instance.id, request=self.request)

    def perform_destroy(self, instance):
        instance_id = instance.id
        instance.delete()
        log_audit(self.request.user, 'role_delete', type_objet='ROLE', id_objet=instance_id, request=self.request)
