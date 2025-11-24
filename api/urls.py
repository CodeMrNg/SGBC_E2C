from django.urls import include, path

from .routes import auth as auth_routes
from .routes import audit as audit_routes
from .routes import organisation as organisation_routes
from .routes import role as role_routes
from .routes import resources as resources_routes

urlpatterns = [
    path('auth/', include((auth_routes.urlpatterns, 'auth'), namespace='auth')),
    path('audit/', include((audit_routes.urlpatterns, 'audit'), namespace='audit')),
    path('', include((organisation_routes.urlpatterns, 'organisation'), namespace='organisation')),
    path('', include((role_routes.urlpatterns, 'role'), namespace='role')),
    path('', include((resources_routes.urlpatterns, 'resources'), namespace='resources')),
]
