#!/usr/bin/env bash
# Entrypoint do backend: espera o Postgres, aplica migrations e roda o seed
# antes de subir o servidor. Tudo idempotente — seguro a cada boot.
set -e

# Aguarda o banco quando DATABASE_URL aponta para um host:porta (ex.: db:5432)
if [ -n "$DATABASE_URL" ]; then
  host_port=$(python - <<'PY'
import os
from urllib.parse import urlparse
u = urlparse(os.environ["DATABASE_URL"])
print(f"{u.hostname or ''} {u.port or 5432}")
PY
)
  host=$(echo "$host_port" | cut -d' ' -f1)
  port=$(echo "$host_port" | cut -d' ' -f2)
  if [ -n "$host" ]; then
    echo "Aguardando o banco em $host:$port..."
    until nc -z "$host" "$port"; do
      sleep 1
    done
    echo "Banco disponível."
  fi
fi

echo "Aplicando migrations..."
python manage.py makemigrations network --noinput
python manage.py migrate --noinput

echo "Rodando seed..."
python manage.py seed_data

echo "Coletando estáticos..."
python manage.py collectstatic --noinput || true

exec "$@"
