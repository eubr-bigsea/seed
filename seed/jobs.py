# coding=utf-8
import logging.config

from flask_babel import gettext
from flask_rq2 import RQ
from seed.models import Deployment, DeploymentLog, DeploymentStatus

logging.config.fileConfig('logging_config.ini')
logger = logging.getLogger(__name__)

rq = RQ()


@rq.exception_handler
def report_jobs_errors(job, *exc_info):
    print job, exc_info

@rq.job
def deploy(deployment_id):
    try:
        deployment = Deployment.query.get(deployment_id)
        if deployment:
            if logger.isEnabledFor(logging.INFO):
                logger.info('Running job for deployment %s', deployment_id)

            return {'status': 'OK', 'message': 'Done'}
        else:
            log = DeploymentLog(
                status=DeploymentStatus.SUSPENDED, deployment_id=deployment_id,
                log=gettext(
                    'Deployment information with id={} not found'.format(
                        deployment_id)))

    except Exception as e:
        return {'status': 'ERROR', 'message': str(e)}
