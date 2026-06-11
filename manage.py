#!/usr/bin/env python
"""Utilitário de linha de comando do Django para o PatchMap."""
import os
import sys


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            'Django não está instalado ou o ambiente virtual não está ativo. '
            'Rode `pip install -r requirements.txt`.'
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
