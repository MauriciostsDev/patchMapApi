"""
Rotas do app network — espelham o contrato em docs/API Backend.md.

  POST   /auth/login      → { token, refresh, user }
  POST   /auth/refresh    → { token }

  GET/POST           /points/       · GET/PUT/PATCH/DELETE /points/:id/
  GET/POST           /panels/       · DELETE /panels/:id/
  GET (read-only)    /sectors/  /switches/  /vlans/
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    ConnectionPointViewSet,
    LoginView,
    PatchPanelViewSet,
    RefreshView,
    SectorViewSet,
    SwitchViewSet,
    VLANViewSet,
)

router = DefaultRouter()
router.register('points', ConnectionPointViewSet, basename='point')
router.register('panels', PatchPanelViewSet, basename='panel')
router.register('sectors', SectorViewSet, basename='sector')
router.register('switches', SwitchViewSet, basename='switch')
router.register('vlans', VLANViewSet, basename='vlan')

urlpatterns = [
    path('auth/login', LoginView.as_view(), name='auth-login'),
    path('auth/refresh', RefreshView.as_view(), name='auth-refresh'),
    path('', include(router.urls)),
]
