# sl_tom

## Setup

The easiest way to get this up and running is to use Docker. Install Docker, copy `local.env.tmpl` to `local.env` and fill in the gaps, then run `docker compose up`. Then you should be able to visit http://localhost:8080/.

## VPS Deployment

This is deployed on a VPS with Podman. Here are the initial commands used to set up the services:

```
podman pod create --name sl_tom -p 443:443

podman run -d --restart=always --pod=sl_tom --name sl_tom-postgres --label "io.containers.autoupdate=image" -v /srv/sl_tom/psql:/var/lib/postgresql/data:z --env-file /srv/sl_tom/postgres.env docker.io/postgres:16

podman run -d --restart=always --pod=sl_tom --name sl_tom-rabbitmq --label "io.containers.autoupdate=image" -v /srv/sl_tom/rabbitmq/:/var/lib/rabbitmq/:z --env-file /srv/sl_tom/rabbitmq.env docker.io/rabbitmq:3

podman run -d --restart=always --pod=sl_tom --name sl_tom-nginx --label "io.containers.autoupdate=image" -v /srv/sl_tom/nginx.conf:/etc/nginx/nginx.conf:ro -v /srv/sl_tom/static/:/srv/sl_tom/static:z -v /srv/sl_tom/media:/srv/sl_tom/media -v /srv/sl_tom/nginx-logs:/var/log/nginx:z -v /etc/tls:/etc/tls:ro docker.io/nginx:1

podman run -d --restart=always --pod=sl_tom --name=sl_tom-django --label "io.containers.autoupdate=image"  --env-file /srv/sl_tom/prod.env -v /srv/sl_tom/static:/srv/sl_tom/static:z -v /srv/sl_tom/astropy:/srv/sl_tom/astropy:z -v /srv/sl_tom/media:/srv/sl_tom/media ghcr.io/cobalt-lensing/sl_tom

# Celery is not set up yet
# podman run -d --restart=always --pod=sl_tom --name=sl_tom-celery --label "io.containers.autoupdate=image"  --env-file /srv/sl_tom/prod.env -v /srv/sl_tom/import:/srv/sl_tom/import:z -v /srv/sl_tom/static:/srv/sl_tom/static:z -v /srv/sl_tom/astropy:/srv/sl_tom/astropy:z -v /srv/sl_tom/media:/srv/sl_tom/media:z ghcr.io/cobalt-lensing/sl_tom bash ./start_worker.sh

cd /etc/systemd/system

podman generate systemd --new --name -f sl_tom

systemctl daemon-reload
systemctl enable pod-sl_tom.service
systemctl start pod-sl_tom.service
```