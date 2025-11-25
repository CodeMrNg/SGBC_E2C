from rest_framework import mixins, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from ..auth_utils import log_audit


class AuditModelViewSet(
    mixins.ListModelMixin,
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    mixins.DestroyModelMixin,
    viewsets.GenericViewSet,
):
    """
    Base viewset with audit logging and partial update support.
    """

    permission_classes = [permissions.IsAuthenticated]
    audit_prefix = ''
    audit_type = ''

    def perform_create(self, serializer):
        instance = serializer.save()
        if self.audit_prefix or self.audit_type:
            log_audit(
                self.request.user,
                f'{self.audit_prefix}_create' if self.audit_prefix else 'create',
                type_objet=self.audit_type or self.__class__.__name__.upper(),
                id_objet=instance.id,
                request=self.request,
            )

    def perform_update(self, serializer):
        instance = serializer.save()
        if self.audit_prefix or self.audit_type:
            log_audit(
                self.request.user,
                f'{self.audit_prefix}_update' if self.audit_prefix else 'update',
                type_objet=self.audit_type or self.__class__.__name__.upper(),
                id_objet=instance.id,
                request=self.request,
            )

    def perform_destroy(self, instance):
        instance_id = instance.id
        instance.delete()
        if self.audit_prefix or self.audit_type:
            log_audit(
                self.request.user,
                f'{self.audit_prefix}_delete' if self.audit_prefix else 'delete',
                type_objet=self.audit_type or self.__class__.__name__.upper(),
                id_objet=instance_id,
                request=self.request,
            )

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    @action(detail=False, methods=['get'], url_path='count')
    def count(self, request):
        """
        Return the total count of resources after applying filters.
        """
        queryset = self.filter_queryset(self.get_queryset())
        return Response({'count': queryset.count()})
