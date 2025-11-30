from django.contrib.auth import get_user_model
from django.db.models import Q
from rest_framework import permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

from ..auth_utils import log_audit
from ..serializers.user import UserManagementSerializer
from .mixins import AuditModelViewSet

User = get_user_model()


class UtilisateurViewSet(AuditModelViewSet):
    serializer_class = UserManagementSerializer
    permission_classes = [permissions.IsAuthenticated]
    audit_prefix = 'user'
    audit_type = 'USER'
    queryset = User.objects.select_related('id_departement', 'id_role').all().order_by('login')

    def get_queryset(self):
        qs = super().get_queryset()
        actif = self.request.GET.get('actif')
        departement = self.request.GET.get('departement_id')
        role = self.request.GET.get('role_id')
        mfa_active = self.request.GET.get('mfa_active')
        search = self.request.GET.get('search')

        if actif is not None:
            qs = qs.filter(is_active=actif.lower() in ['true', '1', 'yes'])
        if departement:
            qs = qs.filter(id_departement_id=departement)
        if role:
            qs = qs.filter(id_role_id=role)
        if mfa_active is not None:
            qs = qs.filter(mfa_active=mfa_active.lower() in ['true', '1', 'yes'])
        if search:
            qs = qs.filter(
                Q(login__icontains=search)
                | Q(email__icontains=search)
                | Q(first_name__icontains=search)
                | Q(last_name__icontains=search)
                | Q(phone__icontains=search)
            )
        return qs

    def _deactivate(self, instance, request):
        """
        Soft-deactivate a user account instead of deleting it.
        """
        if not instance.is_active:
            return False
        instance.is_active = False
        instance.save(update_fields=['is_active', 'updated_at'])
        log_audit(request.user, 'user_deactivate', type_objet=self.audit_type, id_objet=instance.id, request=request)
        return True

    @action(detail=True, methods=['post'], url_path='desactiver')
    def desactiver(self, request, pk=None):
        instance = self.get_object()
        was_active = self._deactivate(instance, request)
        detail = 'Utilisateur déjà désactivé' if not was_active else 'Utilisateur désactivé'
        return Response({'detail': detail}, status=status.HTTP_200_OK)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        was_active = self._deactivate(instance, request)
        if not was_active:
            return Response({'detail': 'Utilisateur déjà désactivé'}, status=status.HTTP_200_OK)
        return Response({'detail': 'Utilisateur désactivé'}, status=status.HTTP_200_OK)
