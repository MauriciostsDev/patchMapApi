"""
Serializers do PatchMap.

Os campos da API são camelCase (sectorId, patchPanelId, switchPort, lastUpdate,
...) para casar exatamente com frontend/src/types.ts, mesmo que os modelos
usem snake_case. O mapeamento é feito via `source=`.
"""
from rest_framework import serializers

from .models import ConnectionPoint, PatchPanel, Sector, Switch, VLAN


class SectorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sector
        fields = ['id', 'name', 'building', 'floor']


class PatchPanelSerializer(serializers.ModelSerializer):
    class Meta:
        model = PatchPanel
        fields = ['id', 'name', 'location', 'ports']


class SwitchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Switch
        fields = ['id', 'name', 'model', 'location', 'ports', 'ip']


class VLANSerializer(serializers.ModelSerializer):
    vlanId = serializers.IntegerField(source='vlan_id')

    class Meta:
        model = VLAN
        fields = ['id', 'vlanId', 'name', 'subnet', 'description']


class ConnectionPointSerializer(serializers.ModelSerializer):
    # id é opcional no POST: se ausente, geramos 'c<n>' no create().
    id = serializers.CharField(required=False)

    sectorId = serializers.PrimaryKeyRelatedField(
        source='sector', queryset=Sector.objects.all()
    )
    patchPanelId = serializers.PrimaryKeyRelatedField(
        source='patch_panel', queryset=PatchPanel.objects.all()
    )
    switchId = serializers.PrimaryKeyRelatedField(
        source='switch', queryset=Switch.objects.all()
    )
    switchPort = serializers.IntegerField(source='switch_port')
    deviceType = serializers.CharField(source='device_type')
    deviceName = serializers.CharField(
        source='device_name', required=False, allow_blank=True, default=''
    )
    macAddress = serializers.CharField(
        source='mac_address', required=False, allow_blank=True, default=''
    )
    ipAddress = serializers.IPAddressField(
        source='ip_address', required=False, allow_null=True, allow_blank=True
    )
    vlanId = serializers.PrimaryKeyRelatedField(
        source='vlan', queryset=VLAN.objects.all(),
        required=False, allow_null=True,
    )
    lastUpdate = serializers.DateField(source='last_update', required=False)

    class Meta:
        model = ConnectionPoint
        fields = [
            'id', 'identifier', 'sectorId', 'patchPanelId', 'port',
            'switchId', 'switchPort', 'deviceType', 'deviceName',
            'macAddress', 'ipAddress', 'vlanId', 'status', 'notes',
            'lastUpdate',
        ]

    def validate_ipAddress(self, value):
        # O frontend pode mandar '' para "sem IP"; normalizamos para None.
        return value or None

    def _next_id(self):
        existing = ConnectionPoint.objects.values_list('id', flat=True)
        max_n = 0
        for pk in existing:
            if pk.startswith('c') and pk[1:].isdigit():
                max_n = max(max_n, int(pk[1:]))
        return f'c{max_n + 1}'

    def create(self, validated_data):
        if not validated_data.get('id'):
            validated_data['id'] = self._next_id()
        if not validated_data.get('last_update'):
            from datetime import date
            validated_data['last_update'] = date.today()
        return super().create(validated_data)
