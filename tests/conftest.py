import json
import os
import pytest
import datetime
import flask_migrate
from seed.app import create_app
from seed.models import (Deployment, db)
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

@pytest.fixture(scope='session')
def app():
    return create_app()

@pytest.fixture(scope='session')
def client(app):
    path = os.path.dirname(os.path.abspath(__name__))
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{path}/test.db'
    app.config['TESTING'] = True
    # import pdb; pdb.set_trace()
    with app.test_client() as client:
        with app.app_context():
            # db = SQLAlchemy(app)
            # migrate = Migrate(app, db) # this

            #flask_migrate.downgrade(revision="base")
            #flask_migrate.upgrade(revision='head')
            client.secret = app.config['SEED_CONFIG']['secret']
            db.session.commit()
        yield client
