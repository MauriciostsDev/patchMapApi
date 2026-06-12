"""
Modelos do PatchMap — espelham frontend/src/types.ts (o contrato de dados).

Decisões:
- PK é CharField (ex.: 's1', 'pp1', 'c1') para casar 1:1 com os IDs do store
  Zustand offline-first. Isso torna o sync e a migração do seed triviais.
- Campos opcionais (`?` no TS) viram null=True/blank=True.
- `last_update` é DateField (data sem hora) — o MVP trafega 'YYYY-MM-DD'.
"""
from django.db import models


class ConnectionStatus(models.TextChoices):
    ATIVO = 'ativo', 'Ativo'
    INATIVO = 'inativo', 'Inativo'
    PROBLEMA = 'problema', 'Problema'


class DeviceType(models.TextChoices):
    DESKTOP = 'Desktop', 'Desktop'
    NOTEBOOK = 'Notebook', 'Notebook'
    TELEFONE_IP = 'Telefone IP', 'Telefone IP'
    IMPRESSORA = 'Impressora', 'Impressora'
    SCANNER = 'Scanner', 'Scanner'
    SERVIDOR = 'Servidor', 'Servidor'
    ACCESS_POINT = 'Access Point', 'Access Point'
    CAMERA_IP = 'Câmera IP', 'Câmera IP'
    OUTRO = 'Outro', 'Outro'


class Sector(models.Model):
    id = models.CharField(max_length=32, primary_key=True)
    name = models.CharField(max_length=120)
    building = models.CharField(max_length=120)
    floor = models.CharField(max_length=60)

    class Meta:
        ordering = ['id']
        verbose_name = 'Setor'
        verbose_name_plural = 'Setores'

    def __str__(self):
        return f'{self.name} ({self.building})'


class PatchPanel(models.Model):
    id = models.CharField(max_length=32, primary_key=True)
    name = models.CharField(max_length=120)
    location = models.CharField(max_length=160)
    ports = models.PositiveIntegerField()

    class Meta:
        ordering = ['id']
        verbose_name = 'Patch Panel'
        verbose_name_plural = 'Patch Panels'

    def __str__(self):
        return self.name


class Switch(models.Model):
    id = models.CharField(max_length=32, primary_key=True)
    name = models.CharField(max_length=120)
    model = models.CharField(max_length=120)
    location = models.CharField(max_length=160)
    ports = models.PositiveIntegerField()
    ip = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['id']
        verbose_name = 'Switch'
        verbose_name_plural = 'Switches'

    def __str__(self):
        return self.name


class VLAN(models.Model):
    id = models.CharField(max_length=32, primary_key=True)
    vlan_id = models.PositiveIntegerField()
    name = models.CharField(max_length=120)
    subnet = models.CharField(max_length=64)
    description = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['vlan_id']
        verbose_name = 'VLAN'
        verbose_name_plural = 'VLANs'

    def __str__(self):
        return f'VLAN {self.vlan_id} — {self.name}'


class ConnectionPoint(models.Model):
    id = models.CharField(max_length=32, primary_key=True)
    identifier = models.CharField(max_length=64)
    sector = models.ForeignKey(
        Sector, on_delete=models.PROTECT, related_name='connections'
    )
    patch_panel = models.ForeignKey(
        PatchPanel, on_delete=models.PROTECT, related_name='connections'
    )
    port = models.PositiveIntegerField()
    switch = models.ForeignKey(
        Switch, on_delete=models.PROTECT, related_name='connections'
    )
    switch_port = models.PositiveIntegerField()
    device_type = models.CharField(max_length=32, choices=DeviceType.choices)
    device_name = models.CharField(max_length=120, blank=True)
    mac_address = models.CharField(max_length=32, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    vlan = models.ForeignKey(
        VLAN, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='connections',
    )
    status = models.CharField(
        max_length=16, choices=ConnectionStatus.choices,
        default=ConnectionStatus.ATIVO,
    )
    notes = models.TextField(blank=True)
    last_update = models.DateField()

    class Meta:
        ordering = ['identifier']
        verbose_name = 'Ponto de Conexão'
        verbose_name_plural = 'Pontos de Conexão'

    def __str__(self):
        return self.identifier
