#!/usr/bin/env python
# -*- coding: utf-8 -*-
import logging
import logging.config

import eventlet
import eventlet.wsgi
import os
import sqlalchemy_utils
import yaml
from flask import Flask, request
from flask_admin import Admin
from flask_babel import get_locale, Babel
from flask_cors import CORS
from flask_restful import Api
from models import db
from seed.deployment_api import DeploymentDetailApi
from seed.deployment_api import DeploymentListApi
from seed.deployment_target_api import DeploymentTargetDetailApi
from seed.deployment_target_api import DeploymentTargetListApi
from seed.jobs import rq

sqlalchemy_utils.i18n.get_locale = get_locale

eventlet.monkey_patch(all=True)
app = Flask(__name__)

rq.init_app(app)
babel = Babel(app)

logging.config.fileConfig('logging_config.ini')

app.secret_key = 'l3m0n4d1'
# Flask Admin 
admin = Admin(app, name='Lemonade Seed', template_mode='bootstrap3')

# CORS
CORS(app, resources={r"/*": {"origins": "*"}})
api = Api(app)

mappings = {
    '/deployments': DeploymentListApi,
    '/deployments/<int:deployment_id>': DeploymentDetailApi,
    '/targets/<int:job_id>/<deployment_target_id>': DeploymentTargetDetailApi,
    '/targets': DeploymentTargetListApi,
}
for path, view in mappings.iteritems():
    api.add_resource(view, path)


@babel.localeselector
def get_locale():
    return request.args.get('lang', 'en')


def main(is_main_module):
    config_file = os.environ.get('SEED_CONFIG')

    os.chdir(os.environ.get('SEED_HOME', '.'))
    logger = logging.getLogger(__name__)
    if config_file:
        with open(config_file) as f:
            config = yaml.load(f)['seed']

        app.config["RESTFUL_JSON"] = {"cls": app.json_encoder}

        server_config = config.get('servers', {})
        app.config['SQLALCHEMY_DATABASE_URI'] = server_config.get(
            'database_url')
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['SQLALCHEMY_POOL_SIZE'] = 10
        app.config['SQLALCHEMY_POOL_RECYCLE'] = 240

        # RQ config
        app.config['RQ_REDIS_URL'] = config['servers']['redis_url']

        app.config.update(config.get('config', {}))
        app.config['SEED_CONFIG'] = config

        db.init_app(app)

        port = int(config.get('port', 5000))
        logger.debug('Running in %s mode', config.get('environment'))

        if is_main_module:
            if config.get('environment', 'dev') == 'dev':
                # admin.add_view(ModelView(Dashboard, db.session))
                app.run(debug=True, port=port)
            else:
                eventlet.wsgi.server(eventlet.listen(('', port)), app)
    else:
        logger.error('Please, set SEED_CONFIG environment variable')
        exit(1)


main(__name__ == '__main__')
