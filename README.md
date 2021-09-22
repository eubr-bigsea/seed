Lemonade Seed
=============

A micro-service aimed to deploy models created in the Lemonade Project.

[WIP]

## Running

Seed requires Python 3.7 or greater. Also, you need the a running MySQL or MariaDB and Redis server running. 

First, clone the repository:

```
% git clone git@github.com:eubr-bigsea/seed.git
```
Change to seed directory, create a virtualenv and activate it:

```
% cd seed
% python3 -m venv venv
% source venv/bin/activate
```
Copy and change the sample configuration:

```
% cp conf/seed.yaml.template seed.yaml
```

Set environment variables (suggestion: create a shell file and add these commands):

```
% export SEED_CONFIG=seed.yaml
% export FLASK_APP=seed.app
% export FLASK_ENV=development
% export PYTHONPATH=.
```

Run the Flask application:

```
flask run  -p 3326
```

## Executing `rq` workers
[`rq`](http://python-rq.org/) is a simple Python library for queueing jobs and processing them in the background with workers.
To start workers, you need to run the command from the Seed project directory:

```
% flask rq worker

```
`rq` will connect to Redis running in the local host. If you want it to connect to a different host, use the following command,
changing the url accordingly.

```
