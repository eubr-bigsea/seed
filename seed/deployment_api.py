import logging
import math
from http import HTTPStatus
from typing import Any, Callable

from flask import current_app
from flask import g as flask_globals
from flask import request
from flask_babel import gettext
from flask_restful import Resource
from marshmallow.exceptions import ValidationError
from sqlalchemy import or_

from seed import jobs
from seed.app_auth import requires_auth, requires_permission
from seed.models import DeploymentStatus as DStatus
from seed.schema import *
from seed.util import get_internal_name, translate_validation

log = logging.getLogger(__name__)
# region Protected


def schedule_deployment_job(deployment_id: int, locale: str, action: Callable):
    user_id = flask_globals.user.id
    return action.queue(deployment_id, locale, user_id, 
        timeout=60, result_ttl=3600)

# endregion


class DeploymentListApi(Resource):
    """ REST API for listing class Deployment """

    def __init__(self):
        self.human_name = gettext('Deployment')

    @requires_auth
    def get(self):
        if request.args.get('fields'):
            only = [f.strip() for f in request.args.get('fields').split(',')]
        else:
            only = ('id', ) if request.args.get(
                'simple', 'false') == 'true' else None
        enabled_filter = request.args.get('enabled')
        if enabled_filter:
            deployments = Deployment.query.filter(
                Deployment.enabled == (enabled_filter != 'false'))
        else:
            deployments = Deployment.query

        sort = request.args.get('sort', 'name')
        if sort not in ['id', 'name', 'type', 'created', 'updated',
                        'current_status']:
            sort = 'name'
        sort_option = getattr(Deployment, sort)
        if request.args.get('asc', 'true') == 'false':
            sort_option = sort_option.desc()
        deployments = deployments.order_by(sort_option)

        page = request.args.get('page') or '1'
        if page is not None and page.isdigit():
            page_size = int(request.args.get('size', 20))
            page = int(page)
            pagination = deployments.paginate(page, page_size, True)
            result = {
                'data': DeploymentListResponseSchema(
                    many=True, only=only).dump(pagination.items),
                'pagination': {
                    'page': page, 'size': page_size,
                    'total': pagination.total,
                    'pages': int(math.ceil(1.0 * pagination.total / page_size))}
            }
        else:
            result = {
                'data': DeploymentListResponseSchema(
                    many=True, only=only).dump(
                    deployments)}

        if log.isEnabledFor(logging.DEBUG):
            log.debug(gettext('Listing %(name)s', name=self.human_name))

        return result

    @requires_auth
    def post(self):
        result = {'status': 'ERROR',
                  'message': gettext("Missing json in the request body")}
        return_code = HTTPStatus.BAD_REQUEST

        if request.json is not None:
            request.json['created'] = datetime.datetime.utcnow().isoformat()
            request.json['updated'] = request.json['created']
            request.json['user_id'] = flask_globals.user.id
            request.json['user_login'] = flask_globals.user.login
            request.json['user_name'] = flask_globals.user.name
            request.json['version'] = 1
            must_deploy = request.json.pop('deploy', 'False') in (
                'True', 'true', 1)

            request_schema = DeploymentCreateRequestSchema()
            response_schema = DeploymentItemResponseSchema()
            try:
                deployment = request_schema.load(request.json)
                if log.isEnabledFor(logging.DEBUG):
                    log.debug(gettext('Adding %s'), self.human_name)

                deployment.internal_name = get_internal_name(deployment)
                db.session.add(deployment)

                db.session.flush()
                if must_deploy:
                    deployment.execution_id = schedule_deployment_job(
                        deployment.id,  flask_globals.user.locale, jobs.deploy)
                    deployment.current_status = DStatus.PENDING
                else:
                    deployment.current_status = DStatus.SAVED
                
                deployment.enabled = True
                db.session.add(deployment)
                db.session.commit()
                result = response_schema.dump(deployment)
                return_code = HTTPStatus.CREATED
            except ValidationError as e:
                result = {
                    'status': 'ERROR',
                    'message': gettext('Invalid data for %(name)s.',
                                       name=self.human_name),
                    'errors': translate_validation(e.messages)
                }
            except Exception as e:
                result = {'status': 'ERROR',
                          'message': gettext("Internal error")}
                return_code = 500
                if current_app.debug:
                    result['debug_detail'] = str(e)

                log.exception(e)
                db.session.rollback()

        return result, return_code


class DeploymentDetailApi(Resource):
    """ REST API for a single instance of class Deployment """

    def __init__(self):
        self.human_name = gettext('Deployment')

    @requires_auth
    def get(self, deployment_id):

        if log.isEnabledFor(logging.DEBUG):
            log.debug(gettext('Retrieving %s (id=%s)'), self.human_name,
                      deployment_id)

        deployment = Deployment.query.get(deployment_id)
        return_code = HTTPStatus.OK
        if deployment is not None:
            result = {
                'status': 'OK',
                'data': [DeploymentItemResponseSchema().dump(
                    deployment)]
            }
        else:
            return_code = HTTPStatus.NOT_FOUND
            result = {
                'status': 'ERROR',
                'message': gettext(
                    '%(name)s not found (id=%(id)s)',
                    name=self.human_name, id=deployment_id)
            }

        return result, return_code

    @requires_auth
    def delete(self, deployment_id: int) -> Any:
        """Disable the deployment, instead of deleting it (soft delete).
        """
        return_code = HTTPStatus.NO_CONTENT
        if log.isEnabledFor(logging.DEBUG):
            log.debug(gettext('Deleting %s (id=%s)'), self.human_name,
                      deployment_id)
        deployment = Deployment.query.get(deployment_id)
        if deployment is not None:
            try:
                if deployment.current_status in [DStatus.DEPLOYED,
                                                 DStatus.DEPLOYED_OLD]:
                    deployment.current_status = DStatus.PENDING_UNDEPLOY
                    schedule_deployment_job(
                        deployment.id, flask_globals.user.locale, jobs.undeploy)
                elif deployment.current_status == DStatus.PENDING_UNDEPLOY:
                    pass  # Nothing to do
                else:
                    deployment.current_status = DStatus.SUSPENDED
                deployment.enabled = False
                db.session.add(deployment)
                db.session.commit()
                result = {
                    'status': 'OK',
                    'message': gettext('%(name)s changed with success!',
                                       name=self.human_name)
                }
            except Exception as e:
                result = {'status': 'ERROR',
                          'message': gettext("Internal error")}
                return_code = HTTPStatus.INTERNAL_SERVER_ERROR
                if current_app.debug:
                    result['debug_detail'] = str(e)
                db.session.rollback()
                log.exception(e)
        else:
            return_code = HTTPStatus.NOT_FOUND
            result = {
                'status': 'ERROR',
                'message': gettext('%(name)s not found (id=%(id)s).',
                                   name=self.human_name, id=deployment_id)
            }
        return result, return_code

    @requires_auth
    def patch(self, deployment_id):
        result = {'status': 'ERROR', 'message': gettext('Insufficient data.')}
        return_code = HTTPStatus.NOT_FOUND

        if log.isEnabledFor(logging.DEBUG):
            log.debug(gettext('Updating %s (id=%s)'), self.human_name,
                      deployment_id)
        if request.json:
            must_deploy = request.json.pop('deploy', 'False') in (
                'True', 'true', 1)
            must_undeploy = request.json.pop('undeploy', 'False') in (
                'True', 'true', 1)

            request_schema = partial_schema_factory(
                DeploymentCreateRequestSchema)
            # Ignore missing fields to allow partial updates
            deployment = request_schema.load(request.json, partial=True)
            response_schema = DeploymentItemResponseSchema()
            try:
                deployment.id = deployment_id
                if (deployment.internal_name is None
                        or deployment.internal_name == ''):
                    # Internal name must be the same (except if empty),
                    # because it is used to update or delete the deployment
                    deployment.internal_name = get_internal_name(deployment)

                deployment = db.session.merge(deployment)
                
                deployment.base_service_url = deployment.target.base_service_url
                db.session.add(deployment)
                db.session.commit()

                if deployment is not None:
                    if must_deploy:
                        if deployment.current_status in [
                                DStatus.PENDING_UNDEPLOY, DStatus.DEPLOYED_OLD, 
                                DStatus.DEPLOYED]:
                            deployment.current_status = DStatus.DEPLOYED_OLD
                        else:
                            deployment.current_status = DStatus.PENDING

                        db.session.add(deployment)
                        db.session.commit()
                        schedule_deployment_job(deployment.id,
                                                flask_globals.user.locale,
                                                jobs.deploy)
                    elif must_undeploy:
                        if deployment.current_status in [
                                DStatus.PENDING_UNDEPLOY, DStatus.DEPLOYED_OLD, 
                                DStatus.DEPLOYED]:
                            deployment.current_status = DStatus.PENDING_UNDEPLOY
                            db.session.add(deployment)
                            db.session.commit()
                            schedule_deployment_job(deployment.id,
                                                flask_globals.user.locale,
                                                jobs.undeploy)
                    else:
                        deployment.current_status = DStatus.DEPLOYED_OLD
                        db.session.add(deployment)
                        db.session.commit()

                    return_code = HTTPStatus.OK
                    result = {
                        'status': 'OK',
                        'message': gettext(
                            '%(n)s (id=%(id)s) was updated with success!',
                            n=self.human_name,
                            id=deployment_id),
                        'data': [response_schema.dump(
                            deployment)]
                    }
            except ValidationError as e:
                result = {
                    'status': 'ERROR',
                    'message': gettext('Invalid data for %(name)s (id=%(id)s)',
                                       name=self.human_name,
                                       id=deployment_id),
                    'errors': translate_validation(e.messages)
                }
            except Exception as e:
                result = {'status': 'ERROR',
                          'message': gettext("Internal error")}
                return_code = 500
                if current_app.debug:
                    result['debug_detail'] = str(e)
                log.exception(e)
                db.session.rollback()
        return result, return_code
