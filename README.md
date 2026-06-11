# PatchMap — Backend (Django + DRF)

API REST do PatchMap. Contrato compartilhado com o frontend em
`frontend/src/types.ts` (IDs string, campos camelCase). Detalhes em
`docs/API Backend.md`.

## Stack

- Django 5.1 + Django REST Framework
- PostgreSQL 16 (via Docker) · SQLite como fallback local
- JWT (`djangorestframework-simplejwt`) · CORS liberado em dev

## Rodar com Docker (recomendado)

A partir da raiz do repositório:

```bash
docker compose up --build backend db
```

O `entrypoint.sh` espera o Postgres, aplica migrations, roda o seed e cria o
superusuário antes de subir o servidor.

- API: http://localhost:8000/
- Admin: http://localhost:8000/admin/ — `admin@patchmap.com` / `123456`

## Rodar localmente (sem Docker)

Usa SQLite quando `DATABASE_URL` não está definido:

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # fish: source .venv/bin/activate.fish
pip install -r requirements.txt
python manage.py makemigrations network
python manage.py migrate
python manage.py seed_data
python manage.py runserver
```

## Estrutura

```
backend/
├── config/              # projeto Django (settings, urls, wsgi/asgi)
├── network/             # app: models, serializers, views, urls, admin
│   └── management/commands/seed_data.py   # seed idempotente (port do seed.ts)
├── Dockerfile · entrypoint.sh · requirements.txt
└── manage.py
```

## Endpoints

Ver `docs/API Backend.md`. Resumo: `/auth/login`, `/auth/refresh`, `/points/`
(CRUD), `/panels/` (CRUD), `/sectors/`, `/switches/`, `/vlans/` (read-only).
Leitura pública; escrita exige JWT.

## Variáveis de ambiente

| Variável | Default | Descrição |
|---|---|---|
| `DATABASE_URL` | — (SQLite) | `postgresql://user:pass@host:5432/db` |
| `DJANGO_DEBUG` | `True` | modo debug |
| `DJANGO_SECRET_KEY` | dev key | trocar em produção |
| `DJANGO_ALLOWED_HOSTS` | localhost,... | hosts permitidos (CSV) |
| `CORS_ALLOW_ALL` | `True` | libera CORS (dev) |
| `SEED_ADMIN_EMAIL` / `SEED_ADMIN_PASSWORD` | admin@patchmap.com / 123456 | superusuário semeado |
