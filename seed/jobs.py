# coding=utf-8
import requests
import json
import logging.config
import os
from pathlib import Path
from shutil import copyfile
from typing import Callable

from flask import current_app
from flask_babel import force_locale
from flask_babel import gettext as babel_gettext
from kubernetes import client, config
from kubernetes.client import ApiClient
from kubernetes.client.api.apps_v1_api import AppsV1Api
from kubernetes.client.exceptions import ApiException

from seed import rq
from seed.k8s_crud import create_deployment, delete_deployment
from seed.models import (Deployment, DeploymentLog,
                         DeploymentStatus, DeploymentTarget,
                         DeploymentTargetType, db)
from seed.util import get_internal_name

logging.config.fileConfig('logging_config.ini')
logger = logging.getLogger(__name__)


def ctx_gettext(locale: str):
    def translate(msg, **variables):
        from seed.app import app
        with app.test_request_context():
            with force_locale(locale):
                return babel_gettext(msg, **variables)

    return translate


def _notify_ui(**data):
    services = current_app.config['SEED_CONFIG']['services']
    if 'stand' in services:
        stand = services.get('stand')
        try:
            resp = requests.post(
                f'{stand.get("url")}/room', data=json.dumps(data),
                headers={'X-Auth-Token': stand.get('auth_token'),
                         'Content-type': 'application/json'})
        except:
            pass


@rq.exception_handler
def report_jobs_errors(job, *exc_info):
    logger.error('ERROR', exc_info[0])


@rq.job
def deploy(deployment_id: int, locale: str, user_id: int) -> None:

    gettext = ctx_gettext(locale)
    deployment = None
    try:
        deployment = Deployment.query.get(deployment_id)
        if deployment:
            deployment_image = deployment.image
            deployment_target = deployment.target
            deployment.internal_name = get_internal_name(deployment)
            deployment.base_service_url = deployment_target.base_service_url

            if logger.isEnabledFor(logging.INFO):
                logger.info(
                    gettext('Running job for deployment %(id)s',
                            id=deployment_id))

            if deployment_target.target_type != DeploymentTargetType.KUBERNETES:
                raise ValueError(
                    gettext('Deployment target %(type)s not supported',
                            deployment_target.type))

            api_apps = _get_api(deployment_target, gettext)

            create_deployment(deployment, deployment_image,
                              deployment_target, api_apps)

            # Copy files to volume path
            # volume_path = deployment_target.volume_path
            # if deployment.assets:
            #     files = deployment.assets.split(',')
            #     for f in files:
            #         dst = volume_path + os.path.basename(f)
            #         copyfile(f, dst)

            deployment.current_status = DeploymentStatus.DEPLOYED
            db.session.add(deployment)

            log_message = gettext(
                'Successfully deployed as a service (port={}'.format(
                    deployment.port))
            _log_message_for_deployment(deployment_id, log_message,
                                        status=DeploymentStatus.DEPLOYED)
            db.session.commit()
        else:
            log_message = gettext(
                'Deployment information with id=%(id)s not found',
                id=deployment_id)
            logger.warn(log_message)

    except ApiException as e:
        if e.status in (404, 409):
            status = json.loads(e.body)
            msg = {
                404: '%(kind)s %(name)s not found.',
                409: '%(kind)s %(name)s already exists.',
            }
            name = status.get('details', {}).get('name')
            kind = status.get('details', {}).get('kind', " ")[:-1]
            log_message = gettext(msg[e.status], kind=kind, name=name)
        else:
            log_message = gettext('Error in deployment: %(error)s',
                                  error=str(e))
        _log_exception(log_message, deployment, e)
    except Exception as e:
        log_message = gettext('Error in deployment: %(error)s', error=str(e))
        _log_exception(log_message, deployment, e)
    finally:
        _notify_ui(event='refresh', room=f'deployment.list.{user_id}',
                   data={}, namespace='/stand')


def _get_api(deployment_target: DeploymentTarget,
             gettext: Callable) -> AppsV1Api:
    """Returns API to connect to Kuberntes

    Args:
        deployment_target (DeploymentTarget): Deployment information

    Returns:
        AppsV1Api: Kubernetes api
    """
    if os.path.exists(os.path.join(Path.home(), '.kube', 'config')):
        # Use local configuration, present in ~/.kube/config
        config.load_kube_config()
        api_apps = client.AppsV1Api()
    elif 'KUBERNETES_SERVICE_HOST' in os.environ:
        # Seed is running inside kubernetes.
        config.load_incluster_config()
        api_apps = client.AppsV1Api()
    else:
        # Use auth and url present in the target to connect to the API
        configuration = client.Configuration()
        configuration.verify_ssl = False
        configuration.debug = False
        auth_info = deployment_target.authentication_info
        if auth_info is None:
            raise ValueError(gettext(
                'No authentication info configured in deployment target'))
        token = json.loads(auth_info).get('token')
        configuration.api_key["authorization"] = f"Bearer {token}"
        configuration.host = deployment_target.url
        api_apps = client.AppsV1Api(ApiClient(configuration))
    return api_apps


@rq.job
def undeploy(deployment_id: int, locale: str, user_id: int) -> None:
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
            api_apps = _get_api(deployment_target, gettext)

            delete_deployment(deployment, deployment_target, api_apps)

            deployment.current_status = DeploymentStatus.SUSPENDED
            db.session.add(deployment)
            db.session.commit()
            # Delete files of the volume path
            # volume_path = deployment_target.volume_path
            # files = deployment.assets.split(',')
            # for f in files:
            #     absolute_patch_file = volume_path + os.path.basename(f)
            #     os.remove(absolute_patch_file)
            log_message = gettext('Successfully deleted deployment.')
            _log_message_for_deployment(deployment_id, log_message,
                                        status=DeploymentStatus.SUSPENDED)
        else:
            log_message = gettext(
                locale, 'Deployment information with id={} not found'.format(
                    deployment_id))

            _log_message_for_deployment(deployment_id, log_message,
                                        status=DeploymentStatus.ERROR)
    except ApiException as e:
        if e.status == 404:
            # If deployment does not exists, undeployment is OK.
            status = json.loads(e.body)
            msg = '%(kind)s %(name)s not found.'

            deployment.current_status = DeploymentStatus.SUSPENDED
            db.session.add(deployment)
            db.session.commit()

            name = status.get('details', {}).get('name')
            kind = status.get('details', {}).get('kind', " ")[:-1]
            log_message = gettext(msg, kind=kind, name=name)
            _log_message_for_deployment(deployment_id, log_message,
                                        status=DeploymentStatus.SUSPENDED)
        else:
            log_message = gettext('Error in deployment: %(error)s',
                                  error=str(e))
            _log_exception(log_message, deployment, e)
    except Exception as e:
        logger.exception('Running job for deployment %s')
        log_message = gettext('Error in deployment: {}'.format(e))
        if deployment:
            deployment.current_status = DeploymentStatus.ERROR
            db.session.add(deployment)
        _log_message_for_deployment(deployment_id, log_message,
                                    status=DeploymentStatus.ERROR)
    finally:
        _notify_ui(event='refresh', room=f'deployment.list.{user_id}',
                   data={}, namespace='/stand')


# @rq.job
# def updeploy(deployment_id, locale):
#     # noinspection PyBroadException

#     gettext = ctx_gettext(locale)
#     deployment = None
#     try:
#         deployment = Deployment.query.get(deployment_id)
#         deployment_target = deployment.target

#         if deployment and deployment_target:
#             if logger.isEnabledFor(logging.INFO) or True:
#                 logger.info('Running job for deployment %s', deployment_id)

#             log_message = gettext('Editing deployment.')
#             log_message_for_deployment(deployment_id, log_message,
#                                        status=DeploymentStatus.EDITING)

#             # Update files of the volume path
#             volume_path = deployment_target.volume_path
#             files = deployment.assets.split(',')
#             for f in files:
#                 dst = volume_path + os.path.basename(f)
#                 copyfile(f, dst)

#             log_message = gettext('Successfully updated deployment.')
#             log_message_for_deployment(deployment_id, log_message,
#                                        status=DeploymentStatus.DEPLOYED)
#         else:
#             log_message = gettext(
#                 locale, 'Deployment information with id={} not found'.format(
#                     deployment_id))

#             log_message_for_deployment(deployment_id, log_message,
#                                        status=DeploymentStatus.ERROR)

#     except Exception as e:
#         logger.exception('Running job for deployment %s')
#         log_message = gettext('Error in deployment: {}'.format(e))
#         if deployment:
#             deployment.current_status = DeploymentStatus.ERROR
#             db.session.add(deployment)
#         log_message_for_deployment(deployment_id, log_message,
#                                    status=DeploymentStatus.ERROR)


def _log_message_for_deployment(deployment_id: int, log_message: str,
                                status: DeploymentStatus) -> None:
    log = DeploymentLog(
        status=status, deployment_id=deployment_id, log=log_message)
    DeploymentLog.query.session.add(log)
    DeploymentLog.query.session.commit()


def _log_exception(log_message: str, deployment: Deployment,
                   e: Exception) -> None:
    logger.exception('Running job for deployment', exc_info=True)
    if deployment:
        deployment.current_status = DeploymentStatus.ERROR
        db.session.add(deployment)
        _log_message_for_deployment(deployment.id, log_message,
                                    status=DeploymentStatus.ERROR)
