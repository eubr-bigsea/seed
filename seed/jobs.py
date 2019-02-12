# coding=utf-8
import logging.config
from seed.models import Deployment
from flask import current_app
from flask_rq2 import RQ

rq = RQ()

logging.config.fileConfig('logging_config.ini')
logger = logging.getLogger(__name__)


@rq.job("deploy", ttl=60, result_ttl=3600)
def deploy():
    print '>>>>>>>>', Deployment.query.all()

    logger.info('Running deploy job')
    return {'status': 'OK', 'message': 'Done'}
