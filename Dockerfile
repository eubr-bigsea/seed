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

RUN apk add --no-cache dumb-init libffi-dev

ENV SEED_HOME /usr/local/seed

COPY --from=pip_builder /usr/local /usr/local

WORKDIR $SEED_HOME
COPY . $SEED_HOME
COPY bin/entrypoint /usr/local/bin/

RUN pybabel compile -d $SEED_HOME/seed/i18n/locales

ENTRYPOINT ["/usr/bin/dumb-init", "--", "/usr/local/bin/entrypoint"]
CMD ["server"]
