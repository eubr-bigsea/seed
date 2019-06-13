# coding=utf-8
import logging.config

from flask_babel import gettext as babel_gettext, force_locale
from seed import app
from seed.app import rq
from seed.models import Deployment, DeploymentLog, DeploymentStatus

logging.config.fileConfig('logging_config.ini')
logger = logging.getLogger(__name__)


def ctx_gettext(locale):
    def translate(msg, **variables):
        with app.app.test_request_context():
            with force_locale(locale):
                return babel_gettext(msg, **variables)

    return translate


@rq.job("deploy", ttl=60, result_ttl=3600)
def deploy():
    print((Deployment.query.all()))


@rq.exception_handler
def report_jobs_errors(job, *exc_info):
    print('ERROR', job, exc_info)


@rq.job
def deploy2(deployment_id):
    deployment = Deployment.query.get(deployment_id)
    print('#' * 20, deployment.id, deployment.created)
    log_message_for_deployment(deployment_id, "Teste", DeploymentStatus.ERROR)


@rq.job
def deploy(deployment_id, locale):
    # noinspection PyBroadException

    gettext = ctx_gettext(locale)
    try:
        deployment = Deployment.query.get(deployment_id)
        if deployment:
            if logger.isEnabledFor(logging.INFO) or True:
                logger.info('Running job for deployment %s', deployment_id)

            log_message = gettext('Successfully deployed as a service')
            log_message_for_deployment(deployment_id, log_message,
                                       status=DeploymentStatus.DEPLOYED)
        else:
            log_message = gettext(
                locale, 'Deployment information with id={} not found'.format(
                    deployment_id))

            log_message_for_deployment(deployment_id, log_message,
                                       status=DeploymentStatus.ERROR)

    except Exception as e:
        logger.exception('Running job for deployment %s')
        log_message = gettext(
            'Error in deployment {}: \n {}'.format(deployment_id, str(e)))
        log_message_for_deployment(deployment_id, log_message,
                                   status=DeploymentStatus.ERROR)


def log_message_for_deployment(deployment_id, log_message, status):
    log = DeploymentLog(
        status=status, deployment_id=deployment_id, log=log_message)
    DeploymentLog.query.session.add(log)
    DeploymentLog.query.session.commit()
