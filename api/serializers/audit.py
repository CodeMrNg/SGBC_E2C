from rest_framework import serializers

from ..models import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    utilisateur_login = serializers.SerializerMethodField()
    utilisateur_email = serializers.SerializerMethodField()

    class Meta:
        model = AuditLog
        fields = [
            'id',
            'action',
            'type_objet',
            'id_objet',
            'timestamp',
            'ip_client',
            'details',
            'id_utilisateur',
            'utilisateur_login',
            'utilisateur_email',
        ]
        read_only_fields = fields

    def get_utilisateur_login(self, obj):
        user = obj.id_utilisateur
        return getattr(user, 'login', None) if user else None

    def get_utilisateur_email(self, obj):
        user = obj.id_utilisateur
        return getattr(user, 'email', None) if user else None
