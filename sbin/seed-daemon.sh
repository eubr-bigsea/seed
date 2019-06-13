#!/usr/bin/env sh

# This script controls the seed server daemon initialization, status reporting
# and termination
# TODO: rotate logs

usage="Usage: seed-daemon.sh (start|docker|stop|status)"

# this sript requires the command parameter
if [ $# -le 0 ]; then
  echo $usage
  exit 1
fi

# parameter option
cmd_option=$1

# if unset set seed_home to seed root dir, without ./sbin
export SEED_HOME=${SEED_HOME:-$(cd $(dirname $0)/..; pwd)}
echo ${SEED_HOME}

# get log directory
export SEED_LOG_DIR=${SEED_LOG_DIR:-${SEED_HOME}/logs}

# get pid directory
export SEED_PID_DIR=${SEED_PID_DIR:-/var/run/}

mkdir -p ${SEED_PID_DIR} ${SEED_LOG_DIR}

# log and pid files
log=${SEED_LOG_DIR}/seed-server-${USER}-${HOSTNAME}.out
pid=${SEED_PID_DIR}/seed-server-${USER}.pid

case $cmd_option in

  (start)
    # set python path
    PYTHONPATH=${SEED_HOME}:${PYTHONPATH} \
      python ${SEED_HOME}/seed/manage.py \
      db upgrade

    PYTHONPATH=${SEED_HOME}:${PYTHONPATH} nohup -- \
      python ${SEED_HOME}/seed/runner/seed_server.py \
      -c ${SEED_HOME}/conf/seed-config.yaml \
      >> $log 2>&1 < /dev/null &
    seed_server_pid=$!

    # persist the pid
    echo $seed_server_pid > $pid

    echo "Stand server started, logging to $log (pid=$seed_server_pid)"
    ;;

  (docker)
    trap "$0 stop" SIGINT SIGTERM
    # set python path
    PYTHONPATH=${SEED_HOME}:${PYTHONPATH} \
      python ${SEED_HOME}/seed/manage.py \
      db upgrade
    # check if the db migration was successful
    if [ $? -eq 0 ]
    then
      echo "DB migration: successful"
    else
      echo "Error on DB migration"
      exit 1
    fi

    PYTHONPATH=${SEED_HOME}:${PYTHONPATH} \
      python ${SEED_HOME}/seed/runner/seed_server.py \
      -c ${SEED_HOME}/conf/seed-config.yaml &
    seed_server_pid=$!

    # persist the pid
    echo $seed_server_pid > $pid

    echo "Stand server started, logging to $log (pid=$seed_server_pid)"
    wait
    ;;

  (stop)
    if [ -f $pid ]; then
      TARGET_ID=$(cat $pid)
      if [[ $(ps -p ${TARGET_ID} -o comm=) =~ "python" ]]; then
        echo "stopping seed server, user=${USER}, hostname=${HOSTNAME}"
        (pkill -SIGTERM -P ${TARGET_ID} && \
          kill -SIGTERM ${TARGET_ID} && \
          rm -f $pid)
      else
        echo "no seed server to stop"
      fi
    else
      echo "no seed server to stop"
    fi
    ;;

  (status)
    if [ -f $pid ]; then
      TARGET_ID=$(cat $pid)
      if [[ $(ps -p ${TARGET_ID} -o comm=) =~ "python" ]]; then
        echo "seed server is running (pid=${TARGET_ID})"
        exit 0
      else
        echo "$pid file is present (pid=${TARGET_ID}) but seed server not running"
        exit 1
      fi
    else
      echo seed server not running.
      exit 2
    fi
    ;;

  (*)
    echo $usage
    exit 1
    ;;
esac
