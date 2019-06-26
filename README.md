Lemonade Seed
=============

A micro-service aimed to deploy models created in the Lemonade Project.

[WIP]

## Running

```
PYTHONPATH=. SEED_CONFIG=../seed.yaml python seed/app.py

```

## Executing `rq` workers
[`rq`](http://python-rq.org/) is a simple Python library for queueing jobs and processing them in the background with workers.
To start workers, you need to run the command from the Seed project directory:

```
$ SEED_CONFIG=../seed.yaml FLASK_APP=seed/app.py flask rq worker
```
`rq` will connect to Redis running in the local host. If you want it to connect to a different host, use the following command,
changing the url accordingly:

```
SEED_CONFIG=../seed.yaml FLASK_APP=seed/app.py python -m flask rq worker -v -n auditing --logging_level DEBUG auditing
```
