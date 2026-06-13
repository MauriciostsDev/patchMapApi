"""
Configuração do Django para o backend do PatchMap.

Contrato compartilhado com o frontend: ver docs/API Backend.md e
frontend/src/types.ts. IDs são strings (ex.: 's1', 'pp1', 'c1') e os campos
da API trafegam em camelCase para casar com o store Zustand offline-first.
"""
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent


def env_bool(name: str, default: bool = False) -> bool:
    return os.environ.get(name, str(default)).lower() in ('1', 'true', 'yes', 'on')


SECRET_KEY = os.environ.get(
    'DJANGO_SECRET_KEY',
    'dev-insecure-key-change-me-in-production',
)

# Produção é o padrão (DEBUG=False). Em dev, defina DJANGO_DEBUG=true.
DEBUG = env_bool('DJANGO_DEBUG', False)

ALLOWED_HOSTS = [
    h.strip() for h in os.environ.get(
        # 10.0.2.2 é o alias do host da máquina visto de dentro do emulador Android.
        # Em produção, defina o domínio/IP da VM em DJANGO_ALLOWED_HOSTS.
        'DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1,0.0.0.0,backend,10.0.2.2'
    ).split(',') if h.strip()
]

# Domínios confiáveis para CSRF (admin atrás de proxy HTTPS). Ex.:
# CSRF_TRUSTED_ORIGINS=https://api.seu-dominio.com
CSRF_TRUSTED_ORIGINS = [
    o.strip() for o in os.environ.get('CSRF_TRUSTED_ORIGINS', '').split(',') if o.strip()
]


# ─────────────────────────────────────────────────────────────────────────────
# Apps
# ─────────────────────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Terceiros
    'rest_framework',
    'corsheaders',
    # Apps do projeto
    'network',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    # WhiteNoise serve os estáticos do admin sem precisar de Nginx para isso.
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'


# ─────────────────────────────────────────────────────────────────────────────
# Banco de dados — PostgreSQL via DATABASE_URL; fallback SQLite p/ dev local
# ─────────────────────────────────────────────────────────────────────────────
def parse_database_url(url: str):
    from urllib.parse import urlparse, unquote

    parsed = urlparse(url)
    return {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': unquote(parsed.path.lstrip('/')),
        'USER': unquote(parsed.username or ''),
        'PASSWORD': unquote(parsed.password or ''),
        'HOST': parsed.hostname or '',
        'PORT': str(parsed.port or ''),
    }


DATABASE_URL = os.environ.get('DATABASE_URL')
if DATABASE_URL:
    DATABASES = {'default': parse_database_url(DATABASE_URL)}
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }


AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'

# WhiteNoise: comprime e versiona os estáticos (admin/DRF) servidos pelo Django.
STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# ─────────────────────────────────────────────────────────────────────────────
# Django REST Framework + JWT
# ─────────────────────────────────────────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ),
}

from datetime import timedelta  # noqa: E402

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=12),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
}


# ─────────────────────────────────────────────────────────────────────────────
# CORS — frontend Expo (web + Metro). Em dev liberamos tudo.
# ─────────────────────────────────────────────────────────────────────────────
CORS_ALLOW_ALL_ORIGINS = env_bool('CORS_ALLOW_ALL', True)
CORS_ALLOWED_ORIGINS = [
    o for o in os.environ.get('CORS_ALLOWED_ORIGINS', '').split(',') if o
]


# Credenciais do superusuário semeado automaticamente (ver management/commands/seed_data)
SEED_ADMIN_EMAIL = os.environ.get('SEED_ADMIN_EMAIL', 'admin@patchmap.com')
SEED_ADMIN_PASSWORD = os.environ.get('SEED_ADMIN_PASSWORD', '123456')


# ─────────────────────────────────────────────────────────────────────────────
# Segurança de produção (ativada quando DEBUG=False)
# ─────────────────────────────────────────────────────────────────────────────
if not DEBUG:
    # Confia no header do reverse proxy (Nginx/Traefik) para detectar HTTPS.
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    # Redireciona p/ HTTPS e marca cookies como secure SOMENTE se houver TLS na
    # frente (defina SECURE_SSL=true no .env quando o proxy servir HTTPS).
    SECURE_SSL = env_bool('SECURE_SSL', False)
    SECURE_SSL_REDIRECT = SECURE_SSL
    SESSION_COOKIE_SECURE = SECURE_SSL
    CSRF_COOKIE_SECURE = SECURE_SSL
    SECURE_HSTS_SECONDS = 31536000 if SECURE_SSL else 0
    SECURE_HSTS_INCLUDE_SUBDOMAINS = SECURE_SSL
    SECURE_HSTS_PRELOAD = SECURE_SSL
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'

    if SECRET_KEY == 'dev-insecure-key-change-me-in-production':
        import warnings
        warnings.warn(
            'DJANGO_SECRET_KEY não definida em produção! '
            'Defina uma chave forte no .env antes de expor a API.'
        )
