# sl_tom

## Setup

The easiest way to get this up and running is to use Docker. Install Docker, copy `local.env.tmpl` to `local.env` and fill in the gaps, then run `docker compose up`. Then you should be able to visit http://localhost:8080/.

## VPS Deployment

This is deployed on a VPS with Podman. Here are the initial commands used to set up the services:

```
podman pod create --name sl_tom -p 80:80

podman run -d --restart=always --pod=sl_tom --name sl_tom-postgres --label "io.containers.autoupdate=image" -v /opt/sl_tom/psql:/var/lib/postgresql/data:z --env-file /opt/sl_tom/postgres.env docker.io/postgres:16

podman run -d --restart=always --pod=sl_tom --name sl_tom-rabbitmq --label "io.containers.autoupdate=image" -v /opt/sl_tom/rabbitmq/:/var/lib/rabbitmq/:z --env-file /opt/sl_tom/rabbitmq.env docker.io/rabbitmq:3

podman run -d --restart=always --pod=sl_tom --name sl_tom-nginx --label "io.containers.autoupdate=image" -v /opt/sl_tom/nginx.conf:/etc/nginx/nginx.conf:ro -v /opt/sl_tom/static/:/opt/sl_tom/static:z -v /opt/sl_tom/media:/opt/sl_tom/media -v /opt/sl_tom/nginx-logs:/var/log/nginx docker.io/nginx:1

podman run -d --restart=always --pod=sl_tom --name=sl_tom-django --label "io.containers.autoupdate=image"  --env-file /opt/sl_tom/prod.env -v /opt/sl_tom/import:/opt/sl_tom/import:z -v /opt/sl_tom/static:/opt/sl_tom/static:z -v /opt/sl_tom/astropy:/opt/sl_tom/astropy:z -v /opt/sl_tom/media:/opt/sl_tom/media ghcr.io/cobalt-lensing/sl_tom

# Celery is not set up yet
# podman run -d --restart=always --pod=sl_tom --name=sl_tom-celery --label "io.containers.autoupdate=image"  --env-file /opt/sl_tom/prod.env -v /opt/sl_tom/import:/opt/sl_tom/import:z -v /opt/sl_tom/static:/opt/sl_tom/static:z -v /opt/sl_tom/astropy:/opt/sl_tom/astropy:z -v /opt/sl_tom/media:/opt/sl_tom/media:z ghcr.io/cobalt-lensing/sl_tom bash ./start_worker.sh

cd /etc/systemd/system

podman generate systemd --new --name -f sl_tom

systemctl daemon-reload
systemctl enable pod-sl_tom.service
systemctl start pod-sl_tom.service
```