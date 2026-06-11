from django.contrib import admin

from .models import ConnectionPoint, PatchPanel, Sector, Switch, VLAN


@admin.register(Sector)
class SectorAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'building', 'floor')
    search_fields = ('name', 'building')


@admin.register(PatchPanel)
class PatchPanelAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'location', 'ports')
    search_fields = ('name', 'location')


@admin.register(Switch)
class SwitchAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'model', 'location', 'ports', 'ip')
    search_fields = ('name', 'model', 'ip')


@admin.register(VLAN)
class VLANAdmin(admin.ModelAdmin):
    list_display = ('id', 'vlan_id', 'name', 'subnet')
    search_fields = ('name', 'subnet')


@admin.register(ConnectionPoint)
class ConnectionPointAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'identifier', 'sector', 'device_type', 'device_name',
        'ip_address', 'status', 'last_update',
    )
    list_filter = ('status', 'device_type', 'sector')
    search_fields = ('identifier', 'device_name', 'ip_address', 'mac_address')
