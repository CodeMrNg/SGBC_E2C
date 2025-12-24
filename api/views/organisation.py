from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from ..auth_utils import log_audit
from ..models import Departement, SignatureUtilisateur, Utilisateur
from ..serializers.organisation import DepartementSerializer, SignatureUtilisateurSerializer


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


class SignatureUtilisateurView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = SignatureUtilisateurSerializer
    parser_classes = [MultiPartParser, FormParser]
    lookup_url_kwarg = 'user_id'

    def get_object(self):
        user_id = self.kwargs.get(self.lookup_url_kwarg)
        user = get_object_or_404(Utilisateur, pk=user_id)
        obj, _ = SignatureUtilisateur.objects.get_or_create(utilisateur=user)
        return obj

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = self.get_serializer(obj)
        return Response({'message': 'Signature rÇ¸cupÇ¸rÇ¸e', 'data': serializer.data}, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = self.get_serializer(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save(utilisateur=obj.utilisateur)
        log_audit(request.user, 'signature_utilisateur_update', type_objet='SIGNATURE_UTILISATEUR', id_objet=obj.id, request=request)
        return Response({'message': 'Signature mise Çÿ jour', 'data': serializer.data}, status=status.HTTP_200_OK)
