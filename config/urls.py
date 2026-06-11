"""Roteamento raiz do PatchMap.

Os endpoints espelham o contrato em docs/API Backend.md, montados na raiz
(`/auth/...`, `/points/`, `/sectors/`, etc.) para casar com o frontend.
"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('network.urls')),
]
