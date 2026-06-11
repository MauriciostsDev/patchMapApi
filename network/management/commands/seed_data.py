"""
Popula o banco com o seed do PatchMap.

Port fiel de frontend/src/data/seed.ts (a fonte de verdade do contrato).
Idempotente: usa update_or_create, então pode rodar a cada boot sem duplicar.
Também garante o superusuário padrão usado no login (admin@patchmap.com).

Uso:
    python manage.py seed_data
"""
from datetime import date

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from network.models import ConnectionPoint, PatchPanel, Sector, Switch, VLAN

SECTORS = [
    ('s1', 'Gabinete', 'Principal', '2º andar'),
    ('s2', 'Secretaria', 'Principal', '1º andar'),
    ('s3', 'Planejamento', 'Principal', '3º andar'),
    ('s4', 'Licitações', 'Principal', '2º andar'),
    ('s5', 'Financeiro', 'Principal', '1º andar'),
    ('s6', 'RH', 'Anexo A', 'Térreo'),
    ('s7', 'TI', 'Anexo B', '1º andar'),
    ('s8', 'Almoxarifado', 'Anexo B', 'Térreo'),
    ('s9', 'Protocolo', 'Principal', 'Térreo'),
    ('s10', 'Ouvidoria', 'Anexo A', '1º andar'),
]

PATCH_PANELS = [
    ('pp1', 'PP-Principal-02', 'Rack Principal 2º andar', 24),
    ('pp2', 'PP-Principal-01', 'Rack Principal 1º andar', 24),
    ('pp3', 'PP-Principal-03', 'Rack Principal 3º andar', 24),
    ('pp4', 'PP-AnexoA', 'Rack Anexo A', 16),
    ('pp5', 'PP-AnexoB', 'Rack Anexo B', 16),
    ('pp6', 'PP-Terreo', 'Rack Térreo Central', 12),
    ('pp7', 'PP-Backup', 'Sala Servidores', 48),
]

SWITCHES = [
    ('sw1', 'SW-Core-01', 'Cisco SG350-28', 'Rack Principal', 28, '10.0.0.1'),
    ('sw2', 'SW-Core-02', 'Cisco SG350-28', 'Rack Principal', 28, '10.0.0.2'),
    ('sw3', 'SW-AnexoA', 'TP-Link T1600G-18TS', 'Rack Anexo A', 16, '10.0.1.1'),
    ('sw4', 'SW-AnexoB', 'TP-Link T1600G-18TS', 'Rack Anexo B', 16, '10.0.1.2'),
    ('sw5', 'SW-Backup', 'Cisco SG350-52', 'Sala Servidores', 48, '10.0.0.254'),
]

VLANS = [
    ('v1', 10, 'Administrativo', '10.10.0.0/24', 'Setores administrativos'),
    ('v2', 20, 'Servidores', '10.20.0.0/24', 'Infraestrutura de servidores'),
    ('v3', 30, 'Telefonia', '10.30.0.0/24', 'VoIP'),
    ('v4', 40, 'Visitantes', '10.40.0.0/24', 'Rede guest isolada'),
    ('v5', 50, 'IoT', '10.50.0.0/24', 'Dispositivos inteligentes'),
    ('v6', 99, 'Gerência', '10.99.0.0/24', 'VLAN de gerenciamento'),
]

# id, identifier, sector, patch_panel, port, switch, switch_port, device_type,
# device_name, mac, ip, vlan, status, notes, last_update
CONNECTIONS = [
    ('c1', 'GAB-01', 's1', 'pp1', 1, 'sw1', 5, 'Desktop', 'DESK-GAB-01', '00:1A:2B:3C:4D:01', '10.10.0.11', 'v1', 'ativo', 'Secretária do Gabinete', '2026-05-15'),
    ('c2', 'GAB-02', 's1', 'pp1', 2, 'sw1', 6, 'Desktop', 'DESK-GAB-02', '00:1A:2B:3C:4D:02', '10.10.0.12', 'v1', 'ativo', '', '2026-05-15'),
    ('c3', 'GAB-03', 's1', 'pp1', 3, 'sw1', 7, 'Telefone IP', 'TEL-GAB-01', '00:1A:2B:3C:4D:03', '10.30.0.5', 'v3', 'ativo', '', '2026-05-10'),
    ('c4', 'GAB-04', 's1', 'pp1', 4, 'sw1', 8, 'Impressora', 'IMP-GAB-01', '00:1A:2B:3C:4D:04', '10.10.0.50', 'v1', 'inativo', 'Aguardando manutenção', '2026-06-01'),
    ('c5', 'SEC-01', 's2', 'pp2', 1, 'sw1', 9, 'Desktop', 'DESK-SEC-01', '00:1A:2B:3C:4D:05', '10.10.0.21', 'v1', 'ativo', '', '2026-05-20'),
    ('c6', 'SEC-02', 's2', 'pp2', 2, 'sw1', 10, 'Desktop', 'DESK-SEC-02', '00:1A:2B:3C:4D:06', '10.10.0.22', 'v1', 'ativo', '', '2026-05-20'),
    ('c7', 'SEC-03', 's2', 'pp2', 3, 'sw1', 11, 'Impressora', 'IMP-SEC-01', '00:1A:2B:3C:4D:07', '10.10.0.51', 'v1', 'ativo', 'HP LaserJet Pro', '2026-05-18'),
    ('c8', 'SEC-04', 's2', 'pp2', 4, 'sw1', 12, 'Telefone IP', 'TEL-SEC-01', '00:1A:2B:3C:4D:08', '10.30.0.6', 'v3', 'ativo', '', '2026-05-12'),
    ('c9', 'PLAN-01', 's3', 'pp3', 1, 'sw2', 5, 'Desktop', 'DESK-PLAN-01', '00:1A:2B:3C:4D:09', '10.10.0.31', 'v1', 'ativo', '', '2026-05-25'),
    ('c10', 'PLAN-02', 's3', 'pp3', 2, 'sw2', 6, 'Notebook', 'NOTE-PLAN-01', '00:1A:2B:3C:4D:10', '10.10.0.32', 'v1', 'ativo', 'Docking station', '2026-05-22'),
    ('c11', 'PLAN-03', 's3', 'pp3', 3, 'sw2', 7, 'Desktop', 'DESK-PLAN-02', '00:1A:2B:3C:4D:11', '10.10.0.33', 'v1', 'problema', 'Intermitência na conexão', '2026-06-08'),
    ('c12', 'LIC-01', 's4', 'pp1', 10, 'sw1', 13, 'Desktop', 'DESK-LIC-01', '00:1A:2B:3C:4D:12', '10.10.0.41', 'v1', 'ativo', '', '2026-05-28'),
    ('c13', 'LIC-02', 's4', 'pp1', 11, 'sw1', 14, 'Desktop', 'DESK-LIC-02', '00:1A:2B:3C:4D:13', '10.10.0.42', 'v1', 'ativo', '', '2026-05-28'),
    ('c14', 'FIN-01', 's5', 'pp2', 10, 'sw1', 15, 'Desktop', 'DESK-FIN-01', '00:1A:2B:3C:4D:14', '10.10.0.51', 'v1', 'ativo', '', '2026-06-02'),
    ('c15', 'FIN-02', 's5', 'pp2', 11, 'sw1', 16, 'Desktop', 'DESK-FIN-02', '00:1A:2B:3C:4D:15', '10.10.0.52', 'v1', 'ativo', '', '2026-06-02'),
    ('c16', 'FIN-03', 's5', 'pp2', 12, 'sw1', 17, 'Impressora', 'IMP-FIN-01', '00:1A:2B:3C:4D:16', '10.10.0.52', 'v1', 'ativo', 'Multifuncional', '2026-06-01'),
    ('c17', 'RH-01', 's6', 'pp4', 1, 'sw3', 5, 'Desktop', 'DESK-RH-01', '00:1A:2B:3C:4D:17', '10.10.0.61', 'v1', 'ativo', '', '2026-05-30'),
    ('c18', 'RH-02', 's6', 'pp4', 2, 'sw3', 6, 'Desktop', 'DESK-RH-02', '00:1A:2B:3C:4D:18', '10.10.0.62', 'v1', 'ativo', '', '2026-05-30'),
    ('c19', 'RH-03', 's6', 'pp4', 3, 'sw3', 7, 'Scanner', 'SCAN-RH-01', '00:1A:2B:3C:4D:19', '10.10.0.70', 'v1', 'ativo', 'Scanner de documentos', '2026-05-28'),
    ('c20', 'TI-01', 's7', 'pp5', 1, 'sw4', 5, 'Desktop', 'DESK-TI-01', '00:1A:2B:3C:4D:20', '10.10.0.71', 'v1', 'ativo', '', '2026-06-05'),
    ('c21', 'TI-02', 's7', 'pp5', 2, 'sw4', 6, 'Notebook', 'NOTE-TI-01', '00:1A:2B:3C:4D:21', '10.10.0.72', 'v1', 'ativo', 'Técnico de campo', '2026-06-03'),
    ('c22', 'TI-SRV-01', 's7', 'pp7', 1, 'sw5', 10, 'Servidor', 'SRV-FILE-01', '00:1A:2B:3C:4D:22', '10.20.0.10', 'v2', 'ativo', 'File Server Principal', '2026-06-01'),
    ('c23', 'TI-SRV-02', 's7', 'pp7', 2, 'sw5', 11, 'Servidor', 'SRV-DB-01', '00:1A:2B:3C:4D:23', '10.20.0.11', 'v2', 'ativo', 'PostgreSQL', '2026-06-01'),
    ('c24', 'ALM-01', 's8', 'pp5', 10, 'sw4', 12, 'Desktop', 'DESK-ALM-01', '00:1A:2B:3C:4D:24', '10.10.0.81', 'v1', 'ativo', '', '2026-05-26'),
    ('c25', 'ALM-02', 's8', 'pp5', 11, 'sw4', 13, 'Scanner', 'SCAN-ALM-01', '00:1A:2B:3C:4D:25', '10.10.0.82', 'v1', 'inativo', 'Equipamento com defeito', '2026-06-07'),
    ('c26', 'PROT-01', 's9', 'pp6', 1, 'sw1', 20, 'Desktop', 'DESK-PROT-01', '00:1A:2B:3C:4D:26', '10.10.0.91', 'v1', 'ativo', '', '2026-06-04'),
    ('c27', 'PROT-02', 's9', 'pp6', 2, 'sw1', 21, 'Desktop', 'DESK-PROT-02', '00:1A:2B:3C:4D:27', '10.10.0.92', 'v1', 'ativo', '', '2026-06-04'),
    ('c28', 'PROT-03', 's9', 'pp6', 3, 'sw1', 22, 'Impressora', 'IMP-PROT-01', '00:1A:2B:3C:4D:28', '10.10.0.93', 'v1', 'ativo', 'Etiquetadora', '2026-06-02'),
    ('c29', 'OUV-01', 's10', 'pp4', 10, 'sw3', 12, 'Desktop', 'DESK-OUV-01', '00:1A:2B:3C:4D:29', '10.10.0.101', 'v1', 'ativo', '', '2026-05-29'),
    ('c30', 'OUV-02', 's10', 'pp4', 11, 'sw3', 13, 'Telefone IP', 'TEL-OUV-01', '00:1A:2B:3C:4D:30', '10.30.0.15', 'v3', 'ativo', '', '2026-05-27'),
    ('c31', 'GUEST-01', 's2', 'pp2', 20, 'sw1', 25, 'Access Point', 'AP-GUEST-01', '00:1A:2B:3C:4D:31', '10.40.0.1', 'v4', 'ativo', 'Wi-Fi visitantes', '2026-06-01'),
    ('c32', 'GUEST-02', 's6', 'pp4', 15, 'sw3', 14, 'Access Point', 'AP-GUEST-02', '00:1A:2B:3C:4D:32', '10.40.0.2', 'v4', 'ativo', 'Wi-Fi visitantes Anexo A', '2026-06-01'),
    ('c33', 'IOT-01', 's1', 'pp1', 20, 'sw1', 26, 'Câmera IP', 'CAM-GAB-01', '00:1A:2B:3C:4D:33', '10.50.0.10', 'v5', 'ativo', 'Câmera segurança', '2026-05-20'),
    ('c34', 'IOT-02', 's9', 'pp6', 10, 'sw1', 27, 'Câmera IP', 'CAM-PROT-01', '00:1A:2B:3C:4D:34', '10.50.0.11', 'v5', 'ativo', 'Câmera entrada', '2026-05-20'),
]


class Command(BaseCommand):
    help = 'Popula o banco com o seed do PatchMap (idempotente).'

    @transaction.atomic
    def handle(self, *args, **options):
        for sid, name, building, floor in SECTORS:
            Sector.objects.update_or_create(
                id=sid,
                defaults={'name': name, 'building': building, 'floor': floor},
            )

        for pid, name, location, ports in PATCH_PANELS:
            PatchPanel.objects.update_or_create(
                id=pid,
                defaults={'name': name, 'location': location, 'ports': ports},
            )

        for swid, name, model, location, ports, ip in SWITCHES:
            Switch.objects.update_or_create(
                id=swid,
                defaults={
                    'name': name, 'model': model, 'location': location,
                    'ports': ports, 'ip': ip,
                },
            )

        for vid, vlan_id, name, subnet, description in VLANS:
            VLAN.objects.update_or_create(
                id=vid,
                defaults={
                    'vlan_id': vlan_id, 'name': name, 'subnet': subnet,
                    'description': description,
                },
            )

        for row in CONNECTIONS:
            (cid, identifier, sector_id, pp_id, port, sw_id, sw_port,
             device_type, device_name, mac, ip, vlan_id, status, notes,
             last_update) = row
            ConnectionPoint.objects.update_or_create(
                id=cid,
                defaults={
                    'identifier': identifier,
                    'sector_id': sector_id,
                    'patch_panel_id': pp_id,
                    'port': port,
                    'switch_id': sw_id,
                    'switch_port': sw_port,
                    'device_type': device_type,
                    'device_name': device_name,
                    'mac_address': mac,
                    'ip_address': ip or None,
                    'vlan_id': vlan_id,
                    'status': status,
                    'notes': notes,
                    'last_update': date.fromisoformat(last_update),
                },
            )

        self._ensure_admin()

        self.stdout.write(self.style.SUCCESS(
            f'Seed concluído: {Sector.objects.count()} setores, '
            f'{PatchPanel.objects.count()} patch panels, '
            f'{Switch.objects.count()} switches, '
            f'{VLAN.objects.count()} VLANs, '
            f'{ConnectionPoint.objects.count()} conexões.'
        ))

    def _ensure_admin(self):
        User = get_user_model()
        email = settings.SEED_ADMIN_EMAIL
        password = settings.SEED_ADMIN_PASSWORD
        user, created = User.objects.get_or_create(
            username=email,
            defaults={'email': email, 'is_staff': True, 'is_superuser': True},
        )
        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(self.style.SUCCESS(
                f'Superusuário criado: {email}'
            ))
        else:
            self.stdout.write(f'Superusuário já existe: {email}')
