#!/bin/bash -ex

MGMT="python manage.py --settings=sl_tom.settings_production"

$MGMT fetch_classifications --generate

$MGMT prune_stale_aggregations

$MGMT aggregate_targets