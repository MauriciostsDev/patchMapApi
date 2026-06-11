"""
Views do PatchMap.

ViewSets de leitura/escrita para os pontos de conexão (CRUD completo) e
read-only para os recursos de topologia (setores, patch panels, switches,
VLANs). Autenticação JWT em /auth.
"""
from django.contrib.auth import authenticate, get_user_model
from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from .models import ConnectionPoint, PatchPanel, Sector, Switch, VLAN
from .serializers import (
    ConnectionPointSerializer,
    PatchPanelSerializer,
    SectorSerializer,
    SwitchSerializer,
    VLANSerializer,
)

User = get_user_model()


class LoginView(APIView):
    """POST /auth/login  { email, password } → { token, refresh, user }."""

    permission_classes = [AllowAny]

    def post(self, request):
        email = (request.data.get('email') or '').strip()
        password = request.data.get('password') or ''

        if not email or not password:
            return Response(
                {'detail': 'E-mail e senha são obrigatórios.'}, status=400
            )

        # Usuários são criados com username == email (ver seed_data).
        user = authenticate(username=email, password=password)
        if user is None:
            # fallback: localizar por e-mail caso username difira
            try:
                candidate = User.objects.get(email__iexact=email)
                user = authenticate(username=candidate.username, password=password)
            except User.DoesNotExist:
                user = None

        if user is None:
            return Response({'detail': 'Credenciais inválidas.'}, status=401)

        refresh = RefreshToken.for_user(user)
        return Response({
            'token': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'email': user.email or user.username,
                'name': user.get_full_name() or user.username,
            },
        })


class RefreshView(TokenRefreshView):
    """POST /auth/refresh  { refresh } → { access }."""

    permission_classes = [AllowAny]


class SectorViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Sector.objects.all()
    serializer_class = SectorSerializer


class PatchPanelViewSet(viewsets.ModelViewSet):
    queryset = PatchPanel.objects.all()
    serializer_class = PatchPanelSerializer


class SwitchViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Switch.objects.all()
    serializer_class = SwitchSerializer


class VLANViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = VLAN.objects.all()
    serializer_class = VLANSerializer


class ConnectionPointViewSet(viewsets.ModelViewSet):
    queryset = ConnectionPoint.objects.select_related(
        'sector', 'patch_panel', 'switch', 'vlan'
    )
    serializer_class = ConnectionPointSerializer
