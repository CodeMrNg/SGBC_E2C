from typing import Optional

from django.utils.deprecation import MiddlewareMixin

from .auth_utils import get_client_ip, log_audit


class AuditAllMiddleware(MiddlewareMixin):
    """
    Middleware qui journalise chaque requête HTTP entrante (succès ou échec).
    """

    def process_response(self, request, response):
        self._log(request, getattr(response, 'status_code', None), details=getattr(response, 'data', None))
        return response

    def process_exception(self, request, exception):
        self._log(request, status=None, details=str(exception))
        return None

    def _log(self, request, status: Optional[int], details=None):
        try:
            user = getattr(request, 'user', None)
            action = f'HTTP {getattr(request, "method", "")}'.strip()
            path = getattr(request, 'path', '')
            query = request.META.get('QUERY_STRING', '')
            message = f'path={path}'
            if query:
                message += f'?{query}'
            if status is not None:
                message += f' | status={status}'
            ip = get_client_ip(request)
            log_audit(
                user,
                action,
                type_objet='HTTP',
                id_objet=None,
                request=request,
                details=f'{message} | data={details}' if details is not None else message,
            )
        except Exception:
            # Ne jamais bloquer la requête pour un problème de log.
            return None
