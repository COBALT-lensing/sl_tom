#!/bin/bash

if [ "$DJANGO_ENV" == "production" ]; then
  export DJANGO_SETTINGS_MODULE="sltom.settings_production"
  
  echo Applying migrations
  python manage.py migrate --noinput
  if [ ! -d "sltom/static" ]; then
    echo Generating static files
    python manage.py collectstatic --clear --no-input
  fi
  echo Starting production server
  exec gunicorn sltom.wsgi -b 0:8080 --access-logfile - --capture-output
else
  echo Applying migrations
  python manage.py migrate --noinput
  echo Starting development server
  exec python manage.py runserver 0:8080
fi