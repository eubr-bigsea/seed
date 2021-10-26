# -*- coding: utf-8 -*-}
import math
import logging

from seed.app_auth import requires_auth, requires_permission
from flask import request, current_app, g as flask_globals
from flask_restful import Resource
from sqlalchemy import or_
from http import HTTPStatus
from marshmallow.exceptions import ValidationError

from seed.schema import *
from seed.util import translate_validation
from flask_babel import gettext

log = logging.getLogger(__name__)
# region Protected

def schedule_deployment_job(deployment_id, locale):
    from seed import jobs
    # config = current_app.config['SEED_CONFIG']
    # q = Queue(connection=Redis(config['servers']['redis_url']))
    # q.enqueue_call(jobs.deploy, args=(deployment_id,), timeout=60,
    #                result_ttl=3600)
    jobs.deploy.queue(deployment_id, locale)


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

        sort = request.args.get('sort', 'description')
        if sort not in ['description']:
            sort = 'description'
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

            request_schema = DeploymentCreateRequestSchema()
            response_schema = DeploymentItemResponseSchema()
            deployment = request_schema.load(request.json)
            try:
                if log.isEnabledFor(logging.DEBUG):
                    log.debug(gettext('Adding %s'), self.human_name)
                deployment = deployment
                db.session.add(deployment)
                db.session.commit()
                result = response_schema.dump(deployment)
                return_code = HTTPStatus.CREATED
            except ValidationError as e:
                result= {
                   'status': 'ERROR', 
                   'message': gettext('Invalid data for %(name)s.)',
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
    def delete(self, deployment_id):
        return_code = HTTPStatus.NO_CONTENT
        if log.isEnabledFor(logging.DEBUG):
            log.debug(gettext('Deleting %s (id=%s)'), self.human_name,
                      deployment_id)
        deployment = Deployment.query.get(deployment_id)
        if deployment is not None:
            try:
                db.session.delete(deployment)
                db.session.commit()
                result = {
                    'status': 'OK',
                    'message': gettext('%(name)s deleted with success!',
                                       name=self.human_name)
                }
            except Exception as e:
                result = {'status': 'ERROR',
                          'message': gettext("Internal error")}
                return_code = HTTPStatus.INTERNAL_SERVER_ERROR
                if current_app.debug:
                    result['debug_detail'] = str(e)
                db.session.rollback()
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
            request_schema = partial_schema_factory(
                DeploymentCreateRequestSchema)
            # Ignore missing fields to allow partial updates
            deployment = request_schema.load(request.json, partial=True)
            response_schema = DeploymentItemResponseSchema()
            try:
                deployment.id = deployment_id
                deployment = db.session.merge(deployment)
                db.session.commit()

                if deployment is not None:
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
                result= {
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
                db.session.rollback()
        return result, return_code
