#!/bin/bash

if [ "$DJANGO_ENV" == "production" ]; then
  export DJANGO_SETTINGS_MODULE="sl_tom.settings_production"
  
  echo Applying migrations
  python manage.py migrate --noinput
  if [ ! -d "sl_tom/static" ]; then
    echo Generating static files
    python manage.py collectstatic --clear --no-input
  fi
  echo Starting production server
  exec gunicorn sl_tom.wsgi -b 0:8080 -t 120 --access-logfile - --capture-output
else
  echo Applying migrations
  python manage.py migrate --noinput
  echo Starting development server
  exec python manage.py runserver 0:8080
fi