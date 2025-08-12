#!/bin/bash -x

MGMT="python manage.py"
SETTINGS="--settings=sl_tom.settings_production"

$MGMT fetch_classifications $SETTINGS --generate

$MGMT prune_stale_aggregations $SETTINGS

$MGMT aggregate_targets $SETTINGS