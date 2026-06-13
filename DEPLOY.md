# Deploy do PatchMap API (VM com Docker)

Guia para subir a API numa máquina virtual usando Docker Compose.
Pré-requisitos na VM: **Docker** + **Docker Compose** (`docker compose version`).

## 1. Clonar e configurar

```bash
git clone https://github.com/MauriciostsDev/patchMapApi.git
cd patchMapApi
cp .env.example .env
nano .env        # ajuste os valores (veja abaixo)
```

No `.env`, no mínimo:

| Variável | O que colocar |
|----------|---------------|
| `POSTGRES_PASSWORD` | senha forte do banco |
| `DJANGO_SECRET_KEY` | `python -c "import secrets;print(secrets.token_urlsafe(64))"` |
| `DJANGO_ALLOWED_HOSTS` | IP público e/ou domínio da VM (ex.: `api.exemplo.com,203.0.113.10`) |
| `SEED_ADMIN_PASSWORD` | senha do admin (login do app) |

## 2. Subir

```bash
docker compose up -d --build
```

Isso sobe **Postgres** + **Django/Gunicorn**. No primeiro boot ele aplica as
migrations e roda o seed (apenas se o banco estiver vazio — reboots não apagam
dados). A API fica em `http://<ip-da-vm>:8000/`.

Verificar:

```bash
curl http://localhost:8000/points/        # deve listar as conexões
docker compose logs -f backend            # logs do gunicorn
```

Admin do Django: `http://<ip-da-vm>:8000/admin/` (`SEED_ADMIN_EMAIL` / senha do `.env`).

## 3. HTTPS (recomendado para produção)

O Android bloqueia tráfego HTTP "limpo" por padrão. Para o app em produção,
ponha um **proxy reverso com TLS** (Nginx, Caddy ou Traefik) na frente do
Gunicorn e use `https://...` como URL da API no app.

Exemplo mínimo com Caddy (HTTPS automático via Let's Encrypt):

```
# Caddyfile
api.seu-dominio.com {
    reverse_proxy localhost:8000
}
```

Depois, no `.env`: `SECURE_SSL=true` e
`CSRF_TRUSTED_ORIGINS=https://api.seu-dominio.com`, e `docker compose up -d` de novo.

> Sem domínio/HTTPS dá para testar via HTTP, mas o app Android precisará
> permitir cleartext (ver guia de deploy do frontend) — não recomendado em produção.

## 4. Operação

```bash
docker compose ps                                   # status
docker compose logs -f backend                      # logs
docker compose restart backend                      # reiniciar
docker compose down                                 # parar (mantém o volume/dados)
docker compose exec backend python manage.py seed_data   # re-semear (APAGA e recria os dados)
docker compose exec backend python manage.py createsuperuser  # criar outro admin
```

### Atualizar para uma nova versão

```bash
git pull
docker compose up -d --build
```

### Backup do banco

```bash
docker compose exec db pg_dump -U patchmap patchmap > backup_$(date +%F).sql
```

## Desenvolvimento local

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up
# runserver + hot reload, DEBUG=true, Postgres exposto em :5432
```

Ou sem Docker (cai para SQLite):

```bash
python -m venv .venv && source .venv/Scripts/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate && python manage.py seed_data
python manage.py runserver 0.0.0.0:8000
```
