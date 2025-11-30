from rest_framework.routers import DefaultRouter

from ..views.user import UtilisateurViewSet

router = DefaultRouter()
router.register(r'utilisateurs', UtilisateurViewSet, basename='utilisateurs')

urlpatterns = router.urls
