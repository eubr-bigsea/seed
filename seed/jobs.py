# coding=utf-8
import logging.config
import os

import yaml
from flask_babel import gettext as babel_gettext, force_locale
from seed import rq
from seed.models import (Deployment, DeploymentImage, DeploymentTarget,
                         DeploymentLog, DeploymentStatus, db)

from seed.k8s_crud import create_deployment, delete_deployment
from kubernetes import client, config
from shutil import copyfile

logging.config.fileConfig('logging_config.ini')
logger = logging.getLogger(__name__)


def get_config():
    config_file = os.environ.get('SEED_CONFIG')
    if config_file is None:
        raise ValueError(
            'You must inform the SEED_CONF env variable')

    with open(config_file) as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    return config['seed']


def ctx_gettext(locale):
    def translate(msg, **variables):
        from seed.app import app
        with app.test_request_context():
            with force_locale(locale):
                return babel_gettext(msg, **variables)

    return translate


@rq.exception_handler
def report_jobs_errors(job, *exc_info):
    print(('ERROR', job, exc_info))


@rq.job
def deploy(deployment_id, locale):
    # noinspection PyBroadException

    import pdb
    pdb.set_trace()
    gettext = ctx_gettext(locale)
    deployment = None
    try:
        deployment = Deployment.query.get(deployment_id)
        deployment_image = deployment.image
        deployment_target = deployment.target

        if deployment and deployment_image and deployment_target:
            if logger.isEnabledFor(logging.INFO):
                logger.info('Running job for deployment %s', deployment_id)

            # Kubernetes
            config.load_kube_config()
            api_apps = client.AppsV1Api()
            create_deployment(deployment, deployment_image,
                              deployment_target, api_apps)

            # Copy files to volume path
            volume_path = deployment_target.volume_path
            files = deployment.assets.split(',')
            for f in files:
                dst = volume_path + os.path.basename(f)
                copyfile(f, dst)

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
        log_message = gettext('Error in deployment: {}'.format(e))
        if deployment:
            deployment.current_status = DeploymentStatus.ERROR
            db.session.add(deployment)

        log_message_for_deployment(deployment_id, log_message,
                                   status=DeploymentStatus.ERROR)


@rq.job
def undeploy(deployment_id, locale):
    # noinspection PyBroadException

    gettext = ctx_gettext(locale)
    deployment = None
    try:
        deployment = Deployment.query.get(deployment_id)
        deployment_target = deployment.target

        if deployment and deployment_target:
            if logger.isEnabledFor(logging.INFO) or True:
                logger.info('Running job for deployment %s', deployment_id)

            # Kubernetes
            config.load_kube_config()
            api_apps = client.AppsV1Api()
            delete_deployment(deployment, deployment_target, api_apps)

            # Delete files of the volume path
            volume_path = deployment_target.volume_path
            files = deployment.assets.split(',')
            for f in files:
                absolute_patch_file = volume_path + os.path.basename(f)
                os.remove(absolute_patch_file)

            log_message = gettext('Successfully deleted deployment.')
            log_message_for_deployment(deployment_id, log_message,
                                       status=DeploymentStatus.SUSPENDED)
        else:
            log_message = gettext(
                locale, 'Deployment information with id={} not found'.format(
                    deployment_id))

            log_message_for_deployment(deployment_id, log_message,
                                       status=DeploymentStatus.ERROR)

    except Exception as e:
        logger.exception('Running job for deployment %s')
        log_message = gettext('Error in deployment: {}'.format(e))
        if deployment:
            deployment.current_status = DeploymentStatus.ERROR
            db.session.add(deployment)
        log_message_for_deployment(deployment_id, log_message,
                                   status=DeploymentStatus.ERROR)


@rq.job
def updeploy(deployment_id, locale):
    # noinspection PyBroadException

    gettext = ctx_gettext(locale)
    deployment = None
    try:
        deployment = Deployment.query.get(deployment_id)
        deployment_target = deployment.target

        if deployment and deployment_target:
            if logger.isEnabledFor(logging.INFO) or True:
                logger.info('Running job for deployment %s', deployment_id)

            log_message = gettext('Editing deployment.')
            log_message_for_deployment(deployment_id, log_message,
                                       status=DeploymentStatus.EDITING)

            # Update files of the volume path
            volume_path = deployment_target.volume_path
            files = deployment.assets.split(',')
            for f in files:
                dst = volume_path + os.path.basename(f)
                copyfile(f, dst)

            log_message = gettext('Successfully updated deployment.')
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
        log_message = gettext('Error in deployment: {}'.format(e))
        if deployment:
            deployment.current_status = DeploymentStatus.ERROR
            db.session.add(deployment)
        log_message_for_deployment(deployment_id, log_message,
                                   status=DeploymentStatus.ERROR)


def log_message_for_deployment(deployment_id, log_message, status):
    log = DeploymentLog(
        status=status, deployment_id=deployment_id, log=log_message)
    DeploymentLog.query.session.add(log)
    DeploymentLog.query.session.commit()
