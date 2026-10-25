# syntax=docker/dockerfile:1
# EcoTeams — image de production (gunicorn + WhiteNoise). Build : docker build -t ecoteams .
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# 1. Dépendances d'abord : cette couche n'est reconstruite que si requirements-prod.txt change.
COPY requirements-prod.txt .
RUN pip install -r requirements-prod.txt

# 2. Code de l'application.
COPY . .

# 3. Fichiers statiques (variables factices : uniquement pour le build, aucun secret).
RUN DJANGO_DEBUG=False DJANGO_SECRET_KEY=build-only-not-a-secret DJANGO_ALLOWED_HOSTS=localhost \
    python manage.py collectstatic --noinput

# 4. Utilisateur non-root + script exécutable (le sed retire d'éventuelles fins de ligne Windows).
RUN sed -i 's/\r$//' docker/entrypoint.sh \
    && chmod +x docker/entrypoint.sh \
    && useradd --system --uid 10001 --create-home --home-dir /home/app app \
    && mkdir -p /app/media /app/data \
    && chown -R app:app /app/media /app/data

USER app

ENV PORT=8000 \
    DJANGO_DEBUG=False \
    DB_ENGINE=sqlite \
    SQLITE_NAME=data/db.sqlite3

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/healthz/' % os.environ.get('PORT','8000'), timeout=4)"

ENTRYPOINT ["docker/entrypoint.sh"]
CMD ["sh", "-c", "gunicorn config.wsgi:application --bind 0.0.0.0:${PORT} --workers ${WEB_CONCURRENCY:-2} --threads 4 --timeout 90 --access-logfile - --error-logfile -"]
