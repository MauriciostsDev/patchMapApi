"""
Popula o banco com os dados reais do PatchMap (SETHAS).

Fonte: "Pontos sethas - Página1.pdf" — colunas SETOR | PATCH PANEL | ID DE
CONEXÃO | SWITCH. Apenas linhas COMPLETAS (com setor preenchido) foram
importadas: 209 conexões (as demais portas ficaram de fora).

Campos não presentes no PDF ficam vazios/nulos (sem dados fabricados):
VLAN, dispositivo, MAC, IP, prédio/andar, modelo/IP do switch.

Idempotente: limpa as tabelas de topologia/conexões e recria. Mantém o admin.

Uso: python manage.py seed_data
"""
from datetime import date

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from network.models import ConnectionPoint, PatchPanel, Sector, Switch, VLAN

# (id, name, building, floor)
SECTORS = [
    ('s1', 'FEAS', '', ''),
    ('s2', 'COPAS', '', ''),
    ('s3', 'EXPEDIENTE', '', ''),
    ('s4', 'COEPI', '', ''),
    ('s5', 'GSAD', '', ''),
    ('s6', 'SUPI', '', ''),
    ('s7', 'GAB', '', ''),
    ('s8', 'UIAP', '', ''),
    ('s9', 'COMIPI', '', ''),
    ('s10', 'GAB RECEPCCAO', '', ''),
    ('s11', 'UIAG', '', ''),
    ('s12', 'SECRETÁRIA', '', ''),
    ('s13', 'AUDITORIO', '', ''),
    ('s14', 'COPLAN', '', ''),
    ('s15', 'NUDIT', '', ''),
    ('s16', 'COSAN SUPAE', '', ''),
    ('s17', 'SUAS PSE', '', ''),
    ('s18', 'DARK ROOM', '', ''),
    ('s19', 'UCI', '', ''),
    ('s20', 'ASSETI INFRA', '', ''),
    ('s21', 'SUAS PSB', '', ''),
    ('s22', 'COPES', '', ''),
    ('s23', 'SUGEP', '', ''),
    ('s24', 'COSAN SUPROG', '', ''),
    ('s25', 'VIG', '', ''),
    ('s26', 'ASSEJU', '', ''),
]

# (id, name, location, ports)
PATCH_PANELS = [
    ('A', 'Patch Panel A', '', 48),
    ('B', 'Patch Panel B', '', 48),
    ('C', 'Patch Panel C', '', 48),
    ('D', 'Patch Panel D', '', 48),
    ('E', 'Patch Panel E', '', 48),
    ('F', 'Patch Panel F', '', 48),
]

# (id, name, model, location, ports, ip)
SWITCHES = [
    ('sw1', 'CORE', '', '', 48, None),
    ('sw2', 'GEREN-01-SW', '', '', 48, None),
    ('sw3', 'GEREN-02-SW', '', '', 48, None),
    ('sw4', 'GEREN-03-SW', '', '', 48, None),
    ('sw5', 'DIST-01-SW', '', '', 48, None),
    ('sw6', 'DIST-02-SW', '', '', 48, None),
]

# Sem dados de VLAN no PDF.
VLANS = []

# (id, identifier, sector_id, pp_id, port, sw_id, switch_port,
#  device_type, device_name, mac, ip, vlan_id, status, notes, last_update)
CONNECTIONS = [
    ('c1', 'A-01', 's1', 'A', 1, 'sw1', 1, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c65', 'B-17', 's2', 'B', 17, 'sw2', 17, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c2', 'A-02', 's1', 'A', 2, 'sw1', 2, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c34', 'A-34', 's3', 'A', 34, 'sw1', 34, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c66', 'B-18', 's2', 'B', 18, 'sw2', 18, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c35', 'A-35', 's3', 'A', 35, 'sw1', 35, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c67', 'B-19', 's2', 'B', 19, 'sw2', 19, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c36', 'A-36', 's3', 'A', 36, 'sw1', 36, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c68', 'B-20', 's2', 'B', 20, 'sw2', 20, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c37', 'A-37', 's3', 'A', 37, 'sw1', 37, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c69', 'B-21', 's2', 'B', 21, 'sw2', 21, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c38', 'A-38', 's3', 'A', 38, 'sw1', 38, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c70', 'B-22', 's2', 'B', 22, 'sw2', 22, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c39', 'A-39', 's3', 'A', 39, 'sw1', 39, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c71', 'B-23', 's2', 'B', 23, 'sw2', 23, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c72', 'B-24', 's4', 'B', 24, 'sw2', 24, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c9', 'A-09', 's5', 'A', 9, 'sw1', 9, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c73', 'B-25', 's4', 'B', 25, 'sw2', 25, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c105', 'C-09', 's6', 'C', 9, 'sw3', 9, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c10', 'A-10', 's5', 'A', 10, 'sw1', 10, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c42', 'A-42', 's3', 'A', 42, 'sw1', 42, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c74', 'B-26', 's4', 'B', 26, 'sw2', 26, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c106', 'C-10', 's6', 'C', 10, 'sw3', 10, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c11', 'A-11', 's5', 'A', 11, 'sw1', 11, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c43', 'A-43', 's3', 'A', 43, 'sw1', 43, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c75', 'B-27', 's4', 'B', 27, 'sw2', 27, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c107', 'C-11', 's6', 'C', 11, 'sw3', 11, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c12', 'A-12', 's5', 'A', 12, 'sw1', 12, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c76', 'B-28', 's4', 'B', 28, 'sw2', 28, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c108', 'C-12', 's6', 'C', 12, 'sw3', 12, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c77', 'B-29', 's4', 'B', 29, 'sw2', 29, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c109', 'C-13', 's6', 'C', 13, 'sw3', 13, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c46', 'A-46', 's2', 'A', 46, 'sw1', 46, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c78', 'B-30', 's4', 'B', 30, 'sw2', 30, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c110', 'C-14', 's6', 'C', 14, 'sw3', 14, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c15', 'A-15', 's7', 'A', 15, 'sw1', 15, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c47', 'A-47', 's2', 'A', 47, 'sw1', 47, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c79', 'B-31', 's4', 'B', 31, 'sw2', 31, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c16', 'A-16', 's7', 'A', 16, 'sw1', 16, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c48', 'A-48', 's2', 'A', 48, 'sw1', 48, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c80', 'B-32', 's8', 'B', 32, 'sw2', 32, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c17', 'A-17', 's7', 'A', 17, 'sw1', 17, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c49', 'B-01', 's2', 'B', 1, 'sw2', 1, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c81', 'B-33', 's8', 'B', 33, 'sw2', 33, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c113', 'C-17', 's9', 'C', 17, 'sw3', 17, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c18', 'A-18', 's7', 'A', 18, 'sw1', 18, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c50', 'B-02', 's2', 'B', 2, 'sw2', 2, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c82', 'B-34', 's8', 'B', 34, 'sw2', 34, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c114', 'C-18', 's9', 'C', 18, 'sw3', 18, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c19', 'A-19', 's10', 'A', 19, 'sw1', 19, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c51', 'B-03', 's2', 'B', 3, 'sw2', 3, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c83', 'B-35', 's8', 'B', 35, 'sw2', 35, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c115', 'C-19', 's11', 'C', 19, 'sw3', 19, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c20', 'A-20', 's10', 'A', 20, 'sw1', 20, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c52', 'B-04', 's2', 'B', 4, 'sw2', 4, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c84', 'B-36', 's8', 'B', 36, 'sw2', 36, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c116', 'C-20', 's11', 'C', 20, 'sw3', 20, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c21', 'A-21', 's10', 'A', 21, 'sw1', 21, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c53', 'B-05', 's2', 'B', 5, 'sw2', 5, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c85', 'B-37', 's8', 'B', 37, 'sw2', 37, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c117', 'C-21', 's11', 'C', 21, 'sw3', 21, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c22', 'A-22', 's10', 'A', 22, 'sw1', 22, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c54', 'B-06', 's2', 'B', 6, 'sw2', 6, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c86', 'B-38', 's8', 'B', 38, 'sw2', 38, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c118', 'C-22', 's11', 'C', 22, 'sw3', 22, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c55', 'B-07', 's2', 'B', 7, 'sw2', 7, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c87', 'B-39', 's8', 'B', 39, 'sw2', 39, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c119', 'C-23', 's11', 'C', 23, 'sw3', 23, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c56', 'B-08', 's2', 'B', 8, 'sw2', 8, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c88', 'B-40', 's8', 'B', 40, 'sw2', 40, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c120', 'C-24', 's11', 'C', 24, 'sw3', 24, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c25', 'A-25', 's12', 'A', 25, 'sw1', 25, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c57', 'B-09', 's2', 'B', 9, 'sw2', 9, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c89', 'B-41', 's8', 'B', 41, 'sw2', 41, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c121', 'C-25', 's11', 'C', 25, 'sw3', 25, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c26', 'A-26', 's12', 'A', 26, 'sw1', 26, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c58', 'B-10', 's2', 'B', 10, 'sw2', 10, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c90', 'B-42', 's8', 'B', 42, 'sw2', 42, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c122', 'C-26', 's11', 'C', 26, 'sw3', 26, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c27', 'A-27', 's13', 'A', 27, 'sw1', 27, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c59', 'B-11', 's2', 'B', 11, 'sw2', 11, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c91', 'B-43', 's8', 'B', 43, 'sw2', 43, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c123', 'C-27', 's11', 'C', 27, 'sw3', 27, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c28', 'A-28', 's13', 'A', 28, 'sw1', 28, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c60', 'B-12', 's2', 'B', 12, 'sw2', 12, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c92', 'B-44', 's8', 'B', 44, 'sw2', 44, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c124', 'C-28', 's11', 'C', 28, 'sw3', 28, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c29', 'A-29', 's13', 'A', 29, 'sw1', 29, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c61', 'B-13', 's2', 'B', 13, 'sw2', 13, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c93', 'B-45', 's8', 'B', 45, 'sw2', 45, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c125', 'C-29', 's14', 'C', 29, 'sw3', 29, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c30', 'A-30', 's13', 'A', 30, 'sw1', 30, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c62', 'B-14', 's2', 'B', 14, 'sw2', 14, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c126', 'C-30', 's14', 'C', 30, 'sw3', 30, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c31', 'A-31', 's13', 'A', 31, 'sw1', 31, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c63', 'B-15', 's2', 'B', 15, 'sw2', 15, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c32', 'A-32', 's13', 'A', 32, 'sw1', 32, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c64', 'B-16', 's2', 'B', 16, 'sw2', 16, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c161', 'D-17', 's15', 'D', 17, 'sw4', 17, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c193', 'E-01', 's16', 'E', 1, 'sw5', 1, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c225', 'E-33', 's17', 'E', 33, 'sw5', 33, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c162', 'D-18', 's15', 'D', 18, 'sw4', 18, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c194', 'E-02', 's16', 'E', 2, 'sw5', 2, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c226', 'E-34', 's17', 'E', 34, 'sw5', 34, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c131', 'C-35', 's14', 'C', 35, 'sw3', 35, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c163', 'D-19', 's15', 'D', 19, 'sw4', 19, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c195', 'E-03', 's16', 'E', 3, 'sw5', 3, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c132', 'C-36', 's14', 'C', 36, 'sw3', 36, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c164', 'D-20', 's15', 'D', 20, 'sw4', 20, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c196', 'E-04', 's16', 'E', 4, 'sw5', 4, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c133', 'C-37', 's14', 'C', 37, 'sw3', 37, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c165', 'D-21', 's15', 'D', 21, 'sw4', 21, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c197', 'E-05', 's16', 'E', 5, 'sw5', 5, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c134', 'C-38', 's14', 'C', 38, 'sw3', 38, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c166', 'D-22', 's15', 'D', 22, 'sw4', 22, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c198', 'E-06', 's16', 'E', 6, 'sw5', 6, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c135', 'C-39', 's14', 'C', 39, 'sw3', 39, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c167', 'D-23', 's15', 'D', 23, 'sw4', 23, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c199', 'E-07', 's16', 'E', 7, 'sw5', 7, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c231', 'E-39', 's17', 'E', 39, 'sw5', 39, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c136', 'C-40', 's14', 'C', 40, 'sw3', 40, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c168', 'D-24', 's15', 'D', 24, 'sw4', 24, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c200', 'E-08', 's16', 'E', 8, 'sw5', 8, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c232', 'E-40', 's17', 'E', 40, 'sw5', 40, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c137', 'C-41', 's18', 'C', 41, 'sw3', 41, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c201', 'E-09', 's16', 'E', 9, 'sw5', 9, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c233', 'E-41', 's17', 'E', 41, 'sw5', 41, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c138', 'C-42', 's18', 'C', 42, 'sw3', 42, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c202', 'E-10', 's16', 'E', 10, 'sw5', 10, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c234', 'E-42', 's17', 'E', 42, 'sw5', 42, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c203', 'E-11', 's16', 'E', 11, 'sw5', 11, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c235', 'E-43', 's17', 'E', 43, 'sw5', 43, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c204', 'E-12', 's16', 'E', 12, 'sw5', 12, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c236', 'E-44', 's17', 'E', 44, 'sw5', 44, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c141', 'C-45', 's18', 'C', 45, 'sw3', 45, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c173', 'D-29', 's19', 'D', 29, 'sw4', 29, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c205', 'E-13', 's16', 'E', 13, 'sw5', 13, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c237', 'E-45', 's17', 'E', 45, 'sw5', 45, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c142', 'C-46', 's18', 'C', 46, 'sw3', 46, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c174', 'D-30', 's19', 'D', 30, 'sw4', 30, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c206', 'E-14', 's16', 'E', 14, 'sw5', 14, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c238', 'E-46', 's17', 'E', 46, 'sw5', 46, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c175', 'D-31', 's19', 'D', 31, 'sw4', 31, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c207', 'E-15', 's16', 'E', 15, 'sw5', 15, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c239', 'E-47', 's17', 'E', 47, 'sw5', 47, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c176', 'D-32', 's19', 'D', 32, 'sw4', 32, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c208', 'E-16', 's16', 'E', 16, 'sw5', 16, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c240', 'E-48', 's17', 'E', 48, 'sw5', 48, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c145', 'D-01', 's20', 'D', 1, 'sw4', 1, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c177', 'D-33', 's19', 'D', 33, 'sw4', 33, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c209', 'E-17', 's21', 'E', 17, 'sw5', 17, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c241', 'F-01', 's17', 'F', 1, 'sw6', 1, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c146', 'D-02', 's20', 'D', 2, 'sw4', 2, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c178', 'D-34', 's19', 'D', 34, 'sw4', 34, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c210', 'E-18', 's21', 'E', 18, 'sw5', 18, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c242', 'F-02', 's17', 'F', 2, 'sw6', 2, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c147', 'D-03', 's20', 'D', 3, 'sw4', 3, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c211', 'E-19', 's21', 'E', 19, 'sw5', 19, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c243', 'F-03', 's17', 'F', 3, 'sw6', 3, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c148', 'D-04', 's20', 'D', 4, 'sw4', 4, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c212', 'E-20', 's21', 'E', 20, 'sw5', 20, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c244', 'F-04', 's17', 'F', 4, 'sw6', 4, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c149', 'D-05', 's22', 'D', 5, 'sw4', 5, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c213', 'E-21', 's21', 'E', 21, 'sw5', 21, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c245', 'F-05', 's17', 'F', 5, 'sw6', 5, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c150', 'D-06', 's22', 'D', 6, 'sw4', 6, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c214', 'E-22', 's21', 'E', 22, 'sw5', 22, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c246', 'F-06', 's17', 'F', 6, 'sw6', 6, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c151', 'D-07', 's22', 'D', 7, 'sw4', 7, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c215', 'E-23', 's21', 'E', 23, 'sw5', 23, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c247', 'F-07', 's1', 'F', 7, 'sw6', 7, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c152', 'D-08', 's22', 'D', 8, 'sw4', 8, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c216', 'E-24', 's21', 'E', 24, 'sw5', 24, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c248', 'F-08', 's1', 'F', 8, 'sw6', 8, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c153', 'D-09', 's22', 'D', 9, 'sw4', 9, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c217', 'E-25', 's21', 'E', 25, 'sw5', 25, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c249', 'F-09', 's23', 'F', 9, 'sw6', 9, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c154', 'D-10', 's22', 'D', 10, 'sw4', 10, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c218', 'E-26', 's21', 'E', 26, 'sw5', 26, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c250', 'F-10', 's23', 'F', 10, 'sw6', 10, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c155', 'D-11', 's22', 'D', 11, 'sw4', 11, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c219', 'E-27', 's21', 'E', 27, 'sw5', 27, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c156', 'D-12', 's22', 'D', 12, 'sw4', 12, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c220', 'E-28', 's21', 'E', 28, 'sw5', 28, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c157', 'D-13', 's22', 'D', 13, 'sw4', 13, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c189', 'D-45', 's16', 'D', 45, 'sw4', 45, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c221', 'E-29', 's21', 'E', 29, 'sw5', 29, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c158', 'D-14', 's22', 'D', 14, 'sw4', 14, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c190', 'D-46', 's16', 'D', 46, 'sw4', 46, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c222', 'E-30', 's21', 'E', 30, 'sw5', 30, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c159', 'D-15', 's22', 'D', 15, 'sw4', 15, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c191', 'D-47', 's16', 'D', 47, 'sw4', 47, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c223', 'E-31', 's21', 'E', 31, 'sw5', 31, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c255', 'F-15', 's24', 'F', 15, 'sw6', 15, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c160', 'D-16', 's22', 'D', 16, 'sw4', 16, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c192', 'D-48', 's16', 'D', 48, 'sw4', 48, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c224', 'E-32', 's21', 'E', 32, 'sw5', 32, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c256', 'F-16', 's24', 'F', 16, 'sw6', 16, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c257', 'F-33', 's23', 'F', 33, 'sw3', 33, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c258', 'F-34', 's23', 'F', 34, 'sw3', 34, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c259', 'F-35', 's25', 'F', 35, 'sw3', 35, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c260', 'F-36', 's25', 'F', 36, 'sw3', 36, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c261', 'F-37', 's25', 'F', 37, 'sw3', 37, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c266', 'F-42', 's26', 'F', 42, 'sw3', 42, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c267', 'F-43', 's26', 'F', 43, 'sw3', 43, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c268', 'F-44', 's26', 'F', 44, 'sw3', 44, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c269', 'F-45', 's26', 'F', 45, 'sw3', 45, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c270', 'F-46', 's26', 'F', 46, 'sw3', 46, 'Outro', '', '', None, None, 'ativo', '', None),
    ('c271', 'F-47', 's26', 'F', 47, 'sw3', 47, 'Outro', '', '', None, None, 'ativo', '', None),
]


class Command(BaseCommand):
    help = 'Popula o banco com os dados reais (SETHAS). Idempotente.'

    @transaction.atomic
    def handle(self, *args, **options):
        # Limpa dados antigos (mock) — conexões primeiro por causa dos FKs.
        ConnectionPoint.objects.all().delete()
        Sector.objects.all().delete()
        PatchPanel.objects.all().delete()
        Switch.objects.all().delete()
        VLAN.objects.all().delete()

        for sid, name, building, floor in SECTORS:
            Sector.objects.create(id=sid, name=name, building=building, floor=floor)

        for pid, name, location, ports in PATCH_PANELS:
            PatchPanel.objects.create(id=pid, name=name, location=location, ports=ports)

        for swid, name, model, location, ports, ip in SWITCHES:
            Switch.objects.create(id=swid, name=name, model=model,
                                  location=location, ports=ports, ip=ip)

        for vid, vlan_id, name, subnet, description in VLANS:
            VLAN.objects.create(id=vid, vlan_id=vlan_id, name=name,
                                subnet=subnet, description=description)

        today = date.today()
        for row in CONNECTIONS:
            (cid, identifier, sector_id, pp_id, port, sw_id, sw_port,
             device_type, device_name, mac, ip, vlan_id, status, notes,
             last_update) = row
            ConnectionPoint.objects.create(
                id=cid, identifier=identifier, sector_id=sector_id,
                patch_panel_id=pp_id, port=port, switch_id=sw_id,
                switch_port=sw_port, device_type=device_type,
                device_name=device_name, mac_address=mac, ip_address=ip,
                vlan_id=vlan_id, status=status, notes=notes,
                last_update=last_update or today,
            )

        self._ensure_admin()
        self.stdout.write(self.style.SUCCESS(
            f'Seed (SETHAS): {Sector.objects.count()} setores, '
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
            self.stdout.write(self.style.SUCCESS(f'Superusuário criado: {email}'))
        else:
            self.stdout.write(f'Superusuário já existe: {email}')
