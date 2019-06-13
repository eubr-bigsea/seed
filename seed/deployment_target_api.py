# -*- coding: utf-8 -*-}
from seed.app_auth import requires_auth
from flask import request, current_app, g as flask_globals
from flask_restful import Resource
from sqlalchemy import or_

import math
import logging
from seed.schema import *
from flask_babel import gettext

log = logging.getLogger(__name__)


def translate_validation(validation_errors):
    for field, errors in list(validation_errors.items()):
        validation_errors[field] = [gettext(error) for error in errors]
    return validation_errors


class DeploymentTargetListApi(Resource):
    """ REST API for listing class DeploymentTarget """

    def __init__(self):
        self.human_name = gettext('DeploymentTarget')

    @requires_auth
    def get(self):
        if request.args.get('fields'):
            only = [f.strip() for f in request.args.get('fields').split(',')]
        else:
            only = ('id', ) if request.args.get(
                'simple', 'false') == 'true' else None
        enabled_filter = request.args.get('enabled')
        if enabled_filter:
            deployment_targets = DeploymentTarget.query.filter(
                DeploymentTarget.enabled == (enabled_filter != 'false'))
        else:
            deployment_targets = DeploymentTarget.query.all()

        page = request.args.get('page') or '1'
        if page is not None and page.isdigit():
            page_size = int(request.args.get('size', 20))
            page = int(page)
            pagination = deployment_targets.paginate(page, page_size, True)
            result = {
                'data': DeploymentTargetListResponseSchema(
                    many=True, only=only).dump(pagination.items).data,
                'pagination': {
                    'page': page, 'size': page_size,
                    'total': pagination.total,
                    'pages': int(math.ceil(1.0 * pagination.total / page_size))}
            }
        else:
            result = {
                'data': DeploymentTargetListResponseSchema(
                    many=True, only=only).dump(
                    deployment_targets).data}

        if log.isEnabledFor(logging.DEBUG):
            log.debug(gettext('Listing %(name)s', name=self.human_name))
        return result

    @requires_auth
    def post(self):
        result = {'status': 'ERROR',
                  'message': gettext("Missing json in the request body")}
        return_code = 400
        
        if request.json is not None:
            request_schema = DeploymentTargetCreateRequestSchema()
            response_schema = DeploymentTargetItemResponseSchema()
            form = request_schema.load(request.json)
            if form.errors:
                result = {'status': 'ERROR',
                          'message': gettext("Validation error"),
                          'errors': translate_validation(form.errors)}
            else:
                try:
                    if log.isEnabledFor(logging.DEBUG):
                        log.debug(gettext('Adding %s'), self.human_name)
                    deployment_target = form.data
                    db.session.add(deployment_target)
                    db.session.commit()
                    result = response_schema.dump(deployment_target).data
                    return_code = 200
                except Exception as e:
                    result = {'status': 'ERROR',
                              'message': gettext("Internal error")}
                    return_code = 500
                    if current_app.debug:
                        result['debug_detail'] = str(e)

                    log.exception(e)
                    db.session.rollback()

        return result, return_code


class DeploymentTargetDetailApi(Resource):
    """ REST API for a single instance of class DeploymentTarget """
    def __init__(self):
        self.human_name = gettext('DeploymentTarget')

    @requires_auth
    def get(self, deployment_target_id):

        if log.isEnabledFor(logging.DEBUG):
            log.debug(gettext('Retrieving %s (id=%s)'), self.human_name,
                      deployment_target_id)

        deployment_target = DeploymentTarget.query.get(deployment_target_id)
        return_code = 200
        if deployment_target is not None:
            result = {
                'status': 'OK',
                'data': [DeploymentTargetItemResponseSchema().dump(
                    deployment_target).data]
            }
        else:
            return_code = 404
            result = {
                'status': 'ERROR',
                'message': gettext(
                    '%(name)s not found (id=%(id)s)',
                    name=self.human_name, id=deployment_target_id)
            }

        return result, return_code

    @requires_auth
    def delete(self, deployment_target_id):
        return_code = 200
        if log.isEnabledFor(logging.DEBUG):
            log.debug(gettext('Deleting %s (id=%s)'), self.human_name,
                      deployment_target_id)
        deployment_target = DeploymentTarget.query.get(deployment_target_id)
        if deployment_target is not None:
            try:
                db.session.delete(deployment_target)
                db.session.commit()
                result = {
                    'status': 'OK',
                    'message': gettext('%(name)s deleted with success!',
                                       name=self.human_name)
                }
            except Exception as e:
                result = {'status': 'ERROR',
                          'message': gettext("Internal error")}
                return_code = 500
                if current_app.debug:
                    result['debug_detail'] = str(e)
                db.session.rollback()
        else:
            return_code = 404
            result = {
                'status': 'ERROR',
                'message': gettext('%(name)s not found (id=%(id)s).',
                                   name=self.human_name, id=deployment_target_id)
            }
        return result, return_code

    @requires_auth
    def patch(self, deployment_target_id):
        result = {'status': 'ERROR', 'message': gettext('Insufficient data.')}
        return_code = 404

        if log.isEnabledFor(logging.DEBUG):
            log.debug(gettext('Updating %s (id=%s)'), self.human_name,
                      deployment_target_id)
        if request.json:
            request_schema = partial_schema_factory(
                DeploymentTargetCreateRequestSchema)
            # Ignore missing fields to allow partial updates
            form = request_schema.load(request.json, partial=True)
            response_schema = DeploymentTargetItemResponseSchema()
            if not form.errors:
                try:
                    form.data.id = deployment_target_id
                    deployment_target = db.session.merge(form.data)
                    db.session.commit()

                    if deployment_target is not None:
                        return_code = 200
                        result = {
                            'status': 'OK',
                            'message': gettext(
                                '%(n)s (id=%(id)s) was updated with success!',
                                n=self.human_name,
                                id=deployment_target_id),
                            'data': [response_schema.dump(
                                deployment_target).data]
                        }
                except Exception as e:
                    result = {'status': 'ERROR',
                              'message': gettext("Internal error")}
                    return_code = 500
                    if current_app.debug:
                        result['debug_detail'] = str(e)
                    db.session.rollback()
            else:
                result = {
                    'status': 'ERROR',
                    'message': gettext('Invalid data for %(name)s (id=%(id)s)',
                                       name=self.human_name,
                                       id=deployment_target_id),
                    'errors': form.errors
                }
        return result, return_code
