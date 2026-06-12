# PatchMap API — Backend (Django + DRF)

API REST do **PatchMap** (rastreador de conexões de rede). Consumida pelo app
mobile no repositório [patchMap](https://github.com/MauriciostsDev/patchMap).
O contrato usa **IDs string** (`s1`, `pp1`, `c1`) e campos **camelCase**
(`sectorId`, `switchPort`, `lastUpdate`) para casar 1:1 com o store do frontend.

## Stack

- Django 5.1 + Django REST Framework
- PostgreSQL 16 (via Docker) · SQLite como fallback local
- JWT (`djangorestframework-simplejwt`) · CORS liberado em dev

## Rodar com Docker (recomendado)

```bash
docker compose up --build
```

Sobe **backend + Postgres**. O `entrypoint.sh` espera o banco, aplica migrations,
roda o seed e cria o superusuário antes de subir o servidor.

- API: http://localhost:8000/
- Admin: http://localhost:8000/admin/ — `admin@patchmap.com` / `123456`

Configuração via `.env` (opcional — veja [`.env.example`](.env.example)); sem
`.env`, usa defaults de desenvolvimento.

## Rodar localmente (sem Docker)

Usa SQLite quando `DATABASE_URL` não está definido:

```bash
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_data
python manage.py runserver 0.0.0.0:8000
```

> Use `0.0.0.0:8000` para que o **emulador Android** alcance a API em
> `http://10.0.2.2:8000` (já incluso em `DJANGO_ALLOWED_HOSTS`).

## Endpoints

| Método | Rota | Auth |
|---|---|---|
| `POST` | `/auth/login` · `/auth/refresh` | pública |
| `GET/POST/PUT/PATCH/DELETE` | `/points/` | leitura pública · escrita JWT |
| `GET/POST/DELETE` | `/panels/` | leitura pública · escrita JWT |
| `GET` | `/sectors/` · `/switches/` · `/vlans/` | pública (read-only) |

Login → `{ token, refresh, user }`. Escrita exige header
`Authorization: Bearer <token>`.

## Seed

`python manage.py seed_data` popula com os **dados reais (SETHAS)**, importados
da planilha "Pontos sethas" (só linhas com setor preenchido): **26 setores,
6 patch panels (A–F), 6 switches, 0 VLANs, 209 conexões** + admin
`admin@patchmap.com / 123456`.

É **idempotente e destrutivo p/ os dados**: limpa setores/painéis/switches/
VLANs/conexões e recria a cada execução (o admin é preservado). Campos ausentes
no PDF ficam nulos (VLAN, dispositivo, MAC, IP, prédio/andar, IP do switch).

## Estrutura

```
.
├── config/              # projeto Django (settings, urls, wsgi/asgi)
├── network/             # app: models, serializers, views, urls, admin
│   └── management/commands/seed_data.py   # seed idempotente
├── Dockerfile · entrypoint.sh · docker-compose.yml
├── requirements.txt · .env.example
└── manage.py
```

## Variáveis de ambiente

| Variável | Default | Descrição |
|---|---|---|
| `DATABASE_URL` | — (SQLite) | `postgresql://user:pass@host:5432/db` |
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | patchmap | usados pelo Postgres no compose |
| `DJANGO_DEBUG` | `True` | modo debug |
| `DJANGO_SECRET_KEY` | dev key | trocar em produção |
| `DJANGO_ALLOWED_HOSTS` | localhost,...,10.0.2.2 | hosts permitidos (CSV) |
| `CORS_ALLOW_ALL` | `True` | libera CORS (dev) |
| `SEED_ADMIN_EMAIL` / `SEED_ADMIN_PASSWORD` | admin@patchmap.com / 123456 | superusuário semeado |

---

Documentação de arquitetura e contrato completo: vault Obsidian no repo
[patchMap/docs](https://github.com/MauriciostsDev/patchMap/tree/main/docs)
(notas *API Backend*, *Modelo de Dados*, *Integração Frontend-Backend*).
