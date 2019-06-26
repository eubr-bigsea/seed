#!/usr/bin/env sh -e

function server
{
  python ${SEED_HOME}/seed/runner/seed_server.py
}

function db_migrate
{
  python ${SEED_HOME}/seed/manage.py db upgrade

  if [ $? -eq 0 ]
  then
    echo "DB migration: successful"
  else
    echo "Error on DB migration"
    exit 1
  fi
}

CMD=$1

# if unset set seed_home to seed root dir, without ./sbin
export SEED_HOME=${SEED_HOME:-$(cd $(dirname $0)/..; pwd)}
export SEED_CONFIG=${SEED_CONFIG:-${SEED_HOME}/conf/seed.yaml}

export FLASK_APP=${FLASK_APP:-${SEED_HOME}/seed/app.py}
export PYTHONPATH=${SEED_HOME}:${PYTHONPATH}

case $CMD in

  (server)
    trap "$0 stop" SIGINT SIGTERM
    db_migrate
    seed_server &
    ;;

  (worker)
    python -m flask rq worker -v -n auditing \
      --logging_level DEBUG auditing &
    ;;

  (*)
    echo "Usage: $0 (server|worker)"
    exit 1
    ;;
esac

wait
