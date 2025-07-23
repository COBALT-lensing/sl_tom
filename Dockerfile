FROM python:3.10

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    netcat-traditional \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# For some reason pipenv can't install psycopg2
RUN pip install \
    pipenv \
    psycopg2

WORKDIR /usr/src/app

COPY Pipfile ./
COPY Pipfile.lock ./

RUN pipenv install --system --dev

COPY . .

ENV PYTHONUNBUFFERED=1

EXPOSE 8080

USER nobody:nogroup

CMD ["bash", "start_server.sh"]