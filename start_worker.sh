#!/bin/bash

if [ "$DJANGO_ENV" == "production" ]; then
  export DJANGO_SETTINGS_MODULE="sl_tom.settings_production"
else
  export WORKER_ARGS="-v3"
fi

exec python manage.py db_worker $WORKER_ARGS