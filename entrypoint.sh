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
python manage.py migrate --noinput

# Seed só roda no primeiro boot (idempotente, mas é destrutivo p/ os dados).
# Para semear manualmente: docker compose exec backend python manage.py seed_data
if [ "${RUN_SEED:-auto}" = "always" ]; then
  echo "Rodando seed (RUN_SEED=always)..."
  python manage.py seed_data
elif [ "${RUN_SEED:-auto}" = "auto" ]; then
  python manage.py shell -c "import sys; from network.models import ConnectionPoint; sys.exit(0 if ConnectionPoint.objects.exists() else 1)" \
    && echo "Banco já populado; pulando seed." \
    || { echo "Banco vazio; rodando seed inicial..."; python manage.py seed_data; }
fi

echo "Coletando estáticos..."
python manage.py collectstatic --noinput || true

exec "$@"
