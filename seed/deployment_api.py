# -*- coding: utf-8 -*-}
import logging

from app_auth import requires_auth
from flask import request, current_app, g as flask_globals
from flask_babel import gettext
from flask_restful import Resource
from schema import *
from seed import jobs

log = logging.getLogger(__name__)


def schedule_deployment_job(deployment_id):
    # config = current_app.config['SEED_CONFIG']
    # q = Queue(connection=Redis(config['servers']['redis_url']))
    # q.enqueue_call(jobs.deploy, args=(deployment_id,), timeout=60,
    #                result_ttl=3600)
    jobs.deploy.queue(deployment_id)


def translate_validation(validation_errors):
    for field, errors in validation_errors.items():
        validation_errors[field] = [gettext(error) for error in errors]
    return validation_errors


class DeploymentListApi(Resource):
    """ REST API for listing class Deployment """

    def __init__(self):
        self.human_name = gettext('Deployment')

    @requires_auth
    def get(self):
        if request.args.get('fields'):
            only = [f.strip() for f in
                    request.args.get('fields').split(',')]
        else:
            only = ('id',) if request.args.get(
                'simple', 'false') == 'true' else None
        enabled_filter = request.args.get('enabled')
        if enabled_filter:
            deployments = Deployment.query.filter(
                Deployment.enabled == (enabled_filter != 'false'))
        else:
            deployments = Deployment.query.all()

        if log.isEnabledFor(logging.DEBUG):
            log.debug(gettext('Listing %s'), self.human_name)
        return {
            'status': 'OK',
            'data': DeploymentListResponseSchema(
                many=True, only=only).dump(deployments).data
        }

    @requires_auth
    def post(self):
        result = {'status': 'ERROR',
                  'message': gettext("Missing json in the request body")}
        return_code = 400
        if request.json is not None:
            request_schema = DeploymentCreateRequestSchema()
            response_schema = DeploymentItemResponseSchema()

            request.json['created'] = datetime.datetime.utcnow().isoformat()
            request.json['updated'] = request.json['created']
            request.json['user_id'] = flask_globals.user.id
            request.json['user_login'] = flask_globals.user.login
            request.json['user_name'] = flask_globals.user.name

            form = request_schema.load(request.json)

            if form.errors:
                result = {'status': 'ERROR',
                          'message': gettext("Validation error"),
                          'errors': translate_validation(form.errors)}
            else:
                try:
                    if log.isEnabledFor(logging.DEBUG):
                        log.debug(gettext('Adding %s'), self.human_name)
                    deployment = form.data

                    db.session.add(deployment)
                    schedule_deployment_job(deployment.id)

                    db.session.commit()
                    result = response_schema.dump(deployment).data
                    return_code = 200
                except Exception as e:
                    result = {'status': 'ERROR',
                              'message': gettext("Internal error")}
                    return_code = 500
                    if current_app.debug:
                        result['debug_detail'] = e.message

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
        return_code = 200
        if deployment is not None:
            result = {
                'status': 'OK',
                'data': [DeploymentItemResponseSchema().dump(deployment).data]
            }
        else:
            return_code = 404
            result = {
                'status': 'ERROR',
                'message': gettext('%s not found (id=%s)', self.human_name,
                                   deployment_id)
            }

        return result, return_code

    @requires_auth
    def delete(self, deployment_id):
        return_code = 200
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
                    'message': gettext('%s deleted with success!',
                                       self.human_name)
                }
            except Exception, e:
                result = {'status': 'ERROR',
                          'message': gettext("Internal error")}
                return_code = 500
                if current_app.debug:
                    result['debug_detail'] = e.message
                db.session.rollback()
        else:
            return_code = 404
            result = {
                'status': 'ERROR',
                'message': gettext('%s not found (id=%s).',
                                   self.human_name,
                                   deployment_id)
            }
        return result, return_code

    @requires_auth
    def patch(self, deployment_id):
        result = {'status': 'ERROR', 'message': gettext('Insufficient data.')}
        return_code = 404

        if log.isEnabledFor(logging.DEBUG):
            log.debug(gettext('Updating %s (id=%s)'), self.human_name,
                      deployment_id)
        if request.json:
            request_schema = partial_schema_factory(
                DeploymentCreateRequestSchema)
            # Ignore missing fields to allow partial updates
            form = request_schema.load(request.json, partial=True)
            response_schema = DeploymentItemResponseSchema()
            if not form.errors:
                try:
                    form.data.id = deployment_id
                    deployment = db.session.merge(form.data)
                    db.session.commit()

                    if deployment is not None:
                        return_code = 200
                        result = {
                            'status': 'OK',
                            'message': gettext(
                                '%s (id=%s) was updated with success!',
                                self.human_name,
                                deployment_id),
                            'data': [response_schema.dump(deployment).data]
                        }
                except Exception as e:
                    result = {'status': 'ERROR',
                              'message': gettext("Internal error")}
                    return_code = 500
                    if current_app.debug:
                        result['debug_detail'] = e.message
                    db.session.rollback()
            else:
                result = {
                    'status': 'ERROR',
                    'message': gettext('Invalid data for %s (id=%s)',
                                       self.human_name,
                                       deployment_id),
                    'errors': form.errors
                }
        return result, return_code
