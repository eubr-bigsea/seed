#!/usr/bin/env python
# -*- coding: utf-8 -*-
# noinspection PyBroadException

try:
    # import eventlet

    # eventlet.monkey_patch(all=True, thread=False)
    pass
except:
    pass

import decimal
import logging
import logging.config
import os

import eventlet.wsgi
import sqlalchemy_utils
import yaml
from flask import Flask, request
from flask.json import JSONEncoder
from flask_babel import Babel, get_locale, gettext
from flask_cors import CORS
from flask_migrate import Migrate
from flask_restful import Api

from seed import rq
from seed.client_api import ClientDetailApi, ClientListApi
from seed.deployment_api import DeploymentDetailApi, DeploymentListApi
from seed.deployment_image_api import (DeploymentImageDetailApi,
                                       DeploymentImageListApi)
from seed.deployment_log_api import (DeploymentLogDetailApi,
                                     DeploymentLogListApi)
from seed.deployment_metric_api import (DeploymentMetricDetailApi,
                                        DeploymentMetricListApi)
from seed.deployment_target_api import (DeploymentTargetDetailApi,
                                        DeploymentTargetListApi)
from seed.models import db


class JsonEncoder(JSONEncoder):
    def default(self, obj):
        if isinstance(obj, decimal.Decimal):
            return float(obj)
        return JSONEncoder.default(self, obj)


def create_babel(app):
    return Babel(app)


def create_app():
    sqlalchemy_utils.i18n.get_locale = get_locale

    # eventlet.monkey_patch(all=True)
    app = Flask(__name__)

    app.json_encoder = JsonEncoder

    babel = create_babel(app)

    logging.config.fileConfig('logging_config.ini')

    app.secret_key = 'l3m0n4d1'

    # CORS
    CORS(app, resources={r"/*": {"origins": "*"}})
    api = Api(app)

    mappings = {
        '/deployments': DeploymentListApi,
        '/deployments/<int:deployment_id>': DeploymentDetailApi,
        '/images/<int:deployment_image_id>': DeploymentImageDetailApi,
        '/images': DeploymentImageListApi,
        '/targets/<int:deployment_target_id>': DeploymentTargetDetailApi,
        '/targets': DeploymentTargetListApi,
        '/clients': ClientListApi,
        '/clients/<int:client_id>': ClientDetailApi,
        '/logs': DeploymentLogListApi,
        '/logs/<int:deployment_log_id>': DeploymentLogDetailApi,
        '/metrics': DeploymentMetricListApi,
        '/metrics/<int:deployment_metric_id>': DeploymentMetricDetailApi,
    }
    for path, view in list(mappings.items()):
        api.add_resource(view, path)
    return app


app = create_app()
babel = create_babel(app)


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

        #migrate = Migrate(app, db)
        migrate = Migrate(app, db, compare_type=True)

        port = int(config.get('port', 5000))
        logger.debug('Running in %s mode', config.get('environment'))
        if is_main_module:
            if config.get('environment', 'dev') == 'dev':
                app.run(debug=True, port=port)
            else:
                eventlet.wsgi.server(eventlet.listen(('', port)), app)
    else:
        logger.error('Please, set SEED_CONFIG environment variable')
        exit(1)


main(__name__ == '__main__')
