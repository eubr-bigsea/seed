FROM python:3.9.5-alpine3.14 as base

FROM base as pip_builder
RUN apk add --no-cache \
      gcc \
      musl-dev \
      libffi-dev \
      openssl-dev \
      g++ \
      postgresql-dev
COPY requirements.txt /
RUN pip install -r /requirements.txt

FROM base
LABEL maintainer="Speed Labs"

RUN apk add --no-cache dumb-init libffi-dev

ENV SEED_HOME /usr/local/seed
ENV SEED_CONFIG $SEED_HOME/conf/seed-config.yaml

COPY --from=pip_builder /usr/local /usr/local

WORKDIR $SEED_HOME
COPY . $SEED_HOME
COPY bin/entrypoint /usr/local/bin/

RUN pybabel compile -d $SEED_HOME/seed/i18n/locales
ENV FLASK_APP seed.app

ENTRYPOINT ["/usr/bin/dumb-init", "--", "/usr/local/bin/entrypoint"]
CMD ["server"]
