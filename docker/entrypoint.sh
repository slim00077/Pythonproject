#!/bin/sh
# Démarrage du conteneur : migrations, comptes facultatifs, puis lancement du serveur.
set -e

echo "[entrypoint] migrations..."
python manage.py migrate --noinput

if [ "${SEED_DEMO_DATA:-0}" = "1" ]; then
    echo "[entrypoint] données de démonstration (idempotent)..."
    python manage.py seed_demo_data --force || echo "[entrypoint] seed_demo_data a échoué (non bloquant)"
fi

if [ -n "${DJANGO_SUPERUSER_USERNAME:-}" ] && [ -n "${DJANGO_SUPERUSER_PASSWORD:-}" ]; then
    echo "[entrypoint] administrateur ${DJANGO_SUPERUSER_USERNAME}..."
    python manage.py createsuperuser --noinput || echo "[entrypoint] administrateur déjà existant"
fi

echo "[entrypoint] démarrage."
exec "$@"
