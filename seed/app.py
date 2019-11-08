#!/usr/bin/env python
# -*- coding: utf-8 -*-
# noinspection PyBroadException
from seed.actuator_api import TMAActuatorApi

try:
    import eventlet

    eventlet.monkey_patch(all=True, thread=False)
except:
    pass

import logging
import logging.config
import os

import eventlet.wsgi
import sqlalchemy_utils
import yaml
from flask import Flask
from flask import request
from flask_admin import Admin
from flask_admin.babel import gettext
from flask_babel import get_locale, Babel
from flask_cors import CORS
from flask_restful import Api
from seed import rq
from seed.deployment_api import DeploymentDetailApi
from seed.deployment_api import DeploymentListApi
from seed.deployment_image_api import DeploymentImageDetailApi
from seed.deployment_image_api import DeploymentImageListApi
from seed.deployment_target_api import DeploymentTargetDetailApi
from seed.deployment_target_api import DeploymentTargetListApi
from seed.models import db
from seed.traceability_api import TraceabilityDetailApi
from seed.traceability_api import TraceabilityListApi

sqlalchemy_utils.i18n.get_locale = get_locale

eventlet.monkey_patch(all=True)
app = Flask(__name__)

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
    '/images/<int:job_id>/<deployment_target_id>': DeploymentImageDetailApi,
    '/images': DeploymentImageListApi,
    '/targets/<int:job_id>/<deployment_target_id>': DeploymentTargetDetailApi,
    '/targets': DeploymentTargetListApi,
    '/traceability': TraceabilityListApi,
    '/traceability/<int:traceability_id>': TraceabilityDetailApi,
    '/actuators': TMAActuatorApi
}
for path, view in list(mappings.items()):
    api.add_resource(view, path)


@babel.localeselector
def get_locale():
    return request.args.get('lang') or \
           request.accept_languages.best_match(['pt', 'en']) or 'pt'


# @requires_auth
# def check_auth():
#     if flask_globals.user.id != 1:
#         abort(401)


def marshmallow_errors():
    """
    Static list of validation errors keys used in marshmallow, required in order
    to extract messages by pybabel
    """
    gettext('Missing data for required field.')
    gettext('Not a valid integer.')
    gettext('Not a valid datetime.')


#


def main(is_main_module):
    config_file = os.environ.get('SEED_CONFIG')

    os.chdir(os.environ.get('SEED_HOME', '.'))
    logger = logging.getLogger(__name__)
    if config_file:
        with open(config_file) as f:
            config = yaml.load(f, Loader=yaml.FullLoader)['seed']

        app.config["RESTFUL_JSON"] = {"cls": app.json_encoder}

        server_config = config.get('servers', {})
        app.config['SQLALCHEMY_DATABASE_URI'] = server_config.get(
            'database_url')
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config['SQLALCHEMY_POOL_SIZE'] = 10
        app.config['SQLALCHEMY_POOL_RECYCLE'] = 240

        app.config['RQ_REDIS_URL'] = config['servers']['redis_url']
        print(app.config['RQ_REDIS_URL'])

        app.config['BABEL_TRANSLATION_DIRECTORIES'] = 'i18n/locales'
        app.config['BABEL_DEFAULT_LOCALE'] = 'UTC'

        app.config.update(config.get('config', {}))
        app.config['SEED_CONFIG'] = config

        db.init_app(app)
        rq.init_app(app)

        # RQ Dashboard
        # app.config.from_object(rq_dashboard.default_settings)
        # app.config.from_object(app.config)
        # app.register_blueprint(rq_dashboard.blueprint, url_prefix='/dashboard')

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
