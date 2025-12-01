from django.db.models import Q
from rest_framework import generics, permissions

from ..auth_utils import log_audit
from ..models import Departement
from ..serializers.organisation import DepartementSerializer


class DepartementListCreateView(generics.ListCreateAPIView):
    serializer_class = DepartementSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = Departement.objects.all()
        actif = self.request.GET.get('actif')
        search = self.request.GET.get('search')
        nom = self.request.GET.get('nom')
        code = self.request.GET.get('code')
        slug = self.request.GET.get('slug')

        if actif is not None:
            if actif.lower() in ['true', '1', 'yes']:
                qs = qs.filter(actif=True)
            elif actif.lower() in ['false', '0', 'no']:
                qs = qs.filter(actif=False)

        if nom:
            qs = qs.filter(nom__icontains=nom)

        if code:
            qs = qs.filter(code__icontains=code)

        if slug:
            qs = qs.filter(slug__icontains=slug)

        if search:
            qs = qs.filter(
                Q(nom__icontains=search) | Q(description__icontains=search) | Q(code__icontains=search) | Q(slug__icontains=search)
            )

        return qs.order_by('nom')

    def perform_create(self, serializer):
        instance = serializer.save()
        log_audit(self.request.user, 'departement_create', type_objet='DEPARTEMENT', id_objet=instance.id, request=self.request)


class DepartementDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = DepartementSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'
    lookup_url_kwarg = 'pk'

    def get_queryset(self):
        return Departement.objects.order_by('nom')

    def perform_update(self, serializer):
        instance = serializer.save()
        log_audit(self.request.user, 'departement_update', type_objet='DEPARTEMENT', id_objet=instance.id, request=self.request)

    def perform_destroy(self, instance):
        instance_id = instance.id
        instance.delete()
        log_audit(self.request.user, 'departement_delete', type_objet='DEPARTEMENT', id_objet=instance_id, request=self.request)
