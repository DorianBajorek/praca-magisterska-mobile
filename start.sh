#!/bin/sh

# Ustawienia, aby skrypt zatrzymywał się w razie błędu
set -e

# Migracje bazy danych
python manage.py makemigrations
python manage.py migrate

python manage.py makemigrations
python manage.py migrate

export DJANGO_SUPERUSER_PASSWORD='sX9.dfUd&^iget'
export DJANGO_SUPERUSER_EMAIL="drugaksiazkabiuro@gmail.com"
export DJANGO_SUPERUSER_USERNAME="drugaksiazkabiuro"
# Uruchamianie serwera aplikacji
python manage.py collectstatic --noinput


exec gunicorn --workers 3 --bind 0.0.0.0:8000 \
    --access-logfile /app/logs/access.log \
    --error-logfile /app/logs/error.log \
    --log-level debug books_service.wsgi:application
