"""
Django settings for the EcoTeams project.

Configuration values are read from environment variables (optionally loaded
from a local ``.env`` file, see ``.env.example``). The database is selected by
``DB_ENGINE=mysql`` (XAMPP) or ``DB_ENGINE=postgresql``; otherwise a local
SQLite database is used as a development fallback.

https://docs.djangoproject.com/en/5.2/topics/settings/
"""

import os
from pathlib import Path

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / '.env')


def env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in ('1', 'true', 'yes', 'on')


def env_list(name, default=''):
    return [item.strip() for item in os.environ.get(name, default).split(',') if item.strip()]


DEBUG = env_bool('DJANGO_DEBUG', default=True)

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', '')
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured('DJANGO_SECRET_KEY doit être défini lorsque DJANGO_DEBUG=False.')
    SECRET_KEY = 'django-insecure-local-development-key-only-change-me'

ALLOWED_HOSTS = env_list('DJANGO_ALLOWED_HOSTS', 'localhost,127.0.0.1,[::1]')
CSRF_TRUSTED_ORIGINS = env_list('DJANGO_CSRF_TRUSTED_ORIGINS')
for _loopback in ('127.0.0.1', 'localhost'):  # container health checks call the app from inside
    if _loopback not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(_loopback)
# Render exposes the public hostname of the service at runtime: trust it without manual configuration.
_render_host = os.environ.get('RENDER_EXTERNAL_HOSTNAME', '').strip()
if _render_host:
    ALLOWED_HOSTS.append(_render_host)
    CSRF_TRUSTED_ORIGINS.append(f'https://{_render_host}')


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    # Shared infrastructure
    'core',
    'organizations',
    'accounts',
    # Member 1 — Teams and memberships
    'teams',
    # Member 2 — Ecological challenges
    'challenges',
    # Member 3 — Ecological actions and validation
    'actions',
    # Member 4 — Goals, points and achievements
    'goals',
    'gamification',
    # Member 5 — Community, notifications and analytics
    'community',
    'notifications',
    'analytics',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
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
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'core.context_processors.navigation',
                'notifications.context_processors.notifications',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

# Défini avant DATABASES car le fuseau de la connexion MySQL s'y aligne
# (voir le commentaire 'TIME_ZONE' dans la branche mysql ci-dessous).
TIME_ZONE = os.environ.get('DJANGO_TIME_ZONE', 'Africa/Tunis')

DB_ENGINE = os.environ.get('DB_ENGINE', 'sqlite').strip().lower()

if DB_ENGINE in ('mysql', 'mariadb', 'mysql-xampp'):
    # Service MySQL/MariaDB fourni par XAMPP. Les identifiants viennent du
    # fichier .env : ils ne doivent jamais être écrits en dur ici.
    #
    # XAMPP embarque MariaDB 10.4, en dessous du minimum exigé par Django 5.2
    # (MariaDB 10.5). 'mysql-xampp' utilise un backend local qui abaisse ce
    # seuil ; après une mise à niveau de MariaDB, repassez sur 'mysql'.
    DATABASES = {
        'default': {
            'ENGINE': (
                'core.db_backends.mysql_xampp'
                if DB_ENGINE == 'mysql-xampp'
                else 'django.db.backends.mysql'
            ),
            'NAME': os.environ.get('DB_NAME', 'ecoteams_db'),
            'USER': os.environ.get('DB_USER', 'ecoteams_user'),
            'PASSWORD': os.environ.get('DB_PASSWORD', ''),
            'HOST': os.environ.get('DB_HOST', '127.0.0.1'),
            'PORT': os.environ.get('DB_PORT', '3306'),
            'CONN_MAX_AGE': int(os.environ.get('DB_CONN_MAX_AGE', '60')),
            # XAMPP ne charge pas les tables de fuseaux horaires de MySQL
            # (mysql.time_zone est vide), donc CONVERT_TZ() renvoie NULL et
            # tout regroupement par jour/semaine remonterait vide. En alignant
            # le fuseau de la connexion sur celui de l'application, Django
            # n'émet plus aucun CONVERT_TZ : les agrégats temporels des
            # tableaux de bord fonctionnent sans installer ces tables.
            # Si vous chargez les tables de fuseaux, mettez DB_TIME_ZONE=UTC.
            'TIME_ZONE': os.environ.get('DB_TIME_ZONE', TIME_ZONE),
            'OPTIONS': {
                'charset': 'utf8mb4',
                # STRICT_TRANS_TABLES fait remonter les troncatures en erreur
                # au lieu de les ignorer silencieusement.
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES', innodb_strict_mode=1",
            },
            'TEST': {
                'CHARSET': 'utf8mb4',
                'COLLATION': 'utf8mb4_unicode_ci',
            },
        }
    }
elif DB_ENGINE in ('postgres', 'postgresql'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('POSTGRES_DB', 'ecoteams'),
            'USER': os.environ.get('POSTGRES_USER', 'ecoteams'),
            'PASSWORD': os.environ.get('POSTGRES_PASSWORD', ''),
            'HOST': os.environ.get('POSTGRES_HOST', 'localhost'),
            'PORT': os.environ.get('POSTGRES_PORT', '5432'),
            'CONN_MAX_AGE': int(os.environ.get('POSTGRES_CONN_MAX_AGE', '60')),
        }
    }
elif DB_ENGINE == 'sqlite':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / os.environ.get('SQLITE_NAME', 'db.sqlite3'),
        }
    }
else:
    raise ImproperlyConfigured("DB_ENGINE doit valoir 'mysql', 'postgresql' ou 'sqlite'.")


# Authentication

AUTH_USER_MODEL = 'accounts.User'
AUTHENTICATION_BACKENDS = ['accounts.backends.EmailOrUsernameModelBackend']
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'analytics:dashboard'
LOGOUT_REDIRECT_URL = 'core:home'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# Internationalization

LANGUAGE_CODE = 'fr-fr'
LANGUAGES = [('fr', 'Français')]
# TIME_ZONE est défini plus haut, avant la section « Database ».
USE_I18N = True
USE_TZ = True


# Static and media files

STATIC_URL = 'static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
if not DEBUG:
    # gunicorn has no static file server: WhiteNoise serves /static/ from STATIC_ROOT (after `collectstatic`).
    MIDDLEWARE.insert(1, 'whitenoise.middleware.WhiteNoiseMiddleware')
    # Compressed (gzip/brotli) static files with long-lived caching headers.
    STORAGES = {
        'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
        'staticfiles': {'BACKEND': 'whitenoise.storage.CompressedStaticFilesStorage'},
    }

MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

ECOTEAMS_MAX_UPLOAD_MB = int(os.environ.get('ECOTEAMS_MAX_UPLOAD_MB', '5'))
FILE_UPLOAD_PERMISSIONS = 0o644


# Security

SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
X_FRAME_OPTIONS = 'DENY'
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_REFERRER_POLICY = 'same-origin'

if env_bool('DJANGO_BEHIND_PROXY', default=False):
    # The platform terminates HTTPS and forwards the original scheme in this header.
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    USE_X_FORWARDED_HOST = True

if not DEBUG:
    SESSION_COOKIE_SECURE = env_bool('DJANGO_SECURE_COOKIES', default=True)
    CSRF_COOKIE_SECURE = env_bool('DJANGO_SECURE_COOKIES', default=True)
    SECURE_SSL_REDIRECT = env_bool('DJANGO_SECURE_SSL_REDIRECT', default=False)
    SECURE_REDIRECT_EXEMPT = [r'^healthz/$']  # probes use plain HTTP inside the container
    # HTTP Strict Transport Security (0 = off). Raise it once HTTPS works everywhere (e.g. 31536000 = 1 year).
    SECURE_HSTS_SECONDS = int(os.environ.get('DJANGO_HSTS_SECONDS', '0'))


# Messages

from django.contrib.messages import constants as message_constants  # noqa: E402

MESSAGE_TAGS = {message_constants.ERROR: 'error'}


# EcoTeams business settings

ECOTEAMS_DEFAULT_ROLE = 'Utilisateur'
ECOTEAMS_TEAM_MILESTONES = [100, 250, 500, 1000, 2500, 5000, 10000]
ECOTEAMS_SUBMISSION_MAX_AGE_DAYS = int(os.environ.get('ECOTEAMS_SUBMISSION_MAX_AGE_DAYS', '30'))
ECOTEAMS_EVENT_REMINDER_HOURS = int(os.environ.get('ECOTEAMS_EVENT_REMINDER_HOURS', '48'))
ECOTEAMS_OLLAMA_URL = os.environ.get('ECOTEAMS_OLLAMA_URL', 'http://127.0.0.1:11434')
ECOTEAMS_OLLAMA_MODEL = os.environ.get('ECOTEAMS_OLLAMA_MODEL', 'phi3:mini')
ECOTEAMS_OLLAMA_TIMEOUT = int(os.environ.get('ECOTEAMS_OLLAMA_TIMEOUT', '120'))


# Coach IA des objectifs (goals/ai.py). Les clés ne sont JAMAIS dans le code : variables d'environnement.
# Fournisseur : « gemini » (GEMINI_API_KEY) ou « anthropic » (ANTHROPIC_API_KEY). Par défaut, Gemini si une
# clé Gemini est définie, sinon Anthropic. Sans clé, la fonctionnalité affiche un message explicite.
GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY') or os.environ.get('GOOGLE_API_KEY') or ''
ECOTEAMS_AI_ENABLED = env_bool('ECOTEAMS_AI_ENABLED', default=True)
ECOTEAMS_AI_PROVIDER = os.environ.get('ECOTEAMS_AI_PROVIDER', '').strip().lower() or (
    'gemini' if GEMINI_API_KEY else 'anthropic'
)
ECOTEAMS_AI_MODEL = os.environ.get('ECOTEAMS_AI_MODEL', '') or (
    'gemini-flash-lite-latest' if ECOTEAMS_AI_PROVIDER == 'gemini' else 'claude-opus-5-5'
)
ECOTEAMS_AI_EFFORT = os.environ.get('ECOTEAMS_AI_EFFORT', 'low')  # Anthropic uniquement
ECOTEAMS_AI_TIMEOUT_SECONDS = float(os.environ.get('ECOTEAMS_AI_TIMEOUT_SECONDS', '45'))
ECOTEAMS_AI_DAILY_LIMIT = int(os.environ.get('ECOTEAMS_AI_DAILY_LIMIT', '10'))
# True : l'appel se fait dans un thread d'arrière-plan (la requête HTTP rend la main tout de suite).
# False : appel synchrone (utilisé par les tests).
ECOTEAMS_AI_BACKGROUND = env_bool('ECOTEAMS_AI_BACKGROUND', default=True)


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {'console': {'class': 'logging.StreamHandler'}},
    'root': {'handlers': ['console'], 'level': 'WARNING'},
    'loggers': {
        'ecoteams': {'handlers': ['console'], 'level': os.environ.get('ECOTEAMS_LOG_LEVEL', 'INFO'), 'propagate': False},
        # 403/404 responses are expected (permission checks); server errors are still logged.
        'django.request': {'handlers': ['console'], 'level': 'ERROR', 'propagate': False},
    },
}
