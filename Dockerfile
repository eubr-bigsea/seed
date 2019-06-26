FROM python:3.7.3-alpine3.9 as base

FROM base as pip_builder
RUN apk add --no-cache \
      gcc \
      musl-dev \
      libffi-dev \
      openssl-dev
COPY requirements.txt /
RUN pip install -r /requirements.txt

FROM base
LABEL maintainer="Speed Labs"

ENV SEED_HOME /usr/local/seed
ENV SEED_CONFIG $SEED_HOME/conf/seed-config.yaml

COPY --from=pip_builder /usr/local /usr/local

WORKDIR $SEED_HOME
COPY . $SEED_HOME

RUN pybabel compile -d $SEED_HOME/seed/i18n/locales

CMD ["/usr/local/seed/sbin/seed-daemon.sh", "docker"]
