# -*- coding: utf-8 -*-}
import math
from app_auth import requires_auth
from flask import request, current_app
from flask_restful import Resource

import logging
from schema import *
from flask_babel import gettext


log = logging.getLogger(__name__)


class DeploymentTargetListApi(Resource):
    """ REST API for listing class DeploymentTarget """

    def __init__(self):
        self.human_name = gettext('DeploymentTarget')

    @requires_auth
    def get(self):
        only = None if request.args.get('simple') != 'true' else ('id',)
        if request.args.get('fields'):
            only = tuple(
                [x.strip() for x in request.args.get('fields').split(',')])

        targets = DeploymentTarget.query

        sort = request.args.get('sort', 'name')
        if sort not in ['name']:
            sort = 'id'
        sort_option = getattr(DeploymentTarget, sort)
        if request.args.get('asc', 'true') == 'false':
            sort_option = sort_option.desc()

        targets = targets.order_by(sort_option)
        q_filter = request.args.get('q')
        if q_filter:
            find_pattern = '%%{}%%'.format(q_filter.replace(" ", "%"))
            targets = targets.filter(or_(
                DeploymentTarget.name.like(find_pattern),
                DeploymentTarget.user_name.like(find_pattern)))

        page = request.args.get('page') or '1'

        if page is not None and page.isdigit():
            page_size = int(request.args.get('size', 20))
            page = int(page)
            pagination = targets.paginate(page, page_size, True)
            result = {
                'data': DeploymentTargetListResponseSchema(many=True, only=only).dump(
                    pagination.items).data,
                'pagination': {
                    'page': page, 'size': page_size,
                    'total': pagination.total,
                    'pages': int(math.ceil(1.0 * pagination.total / page_size))}
            }
        else:
            result = {
                'data': DeploymentTargetListResponseSchema(many=True, only=only).dump(
                    targets).data}
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
                          'errors': form.errors}
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
                        result['debug_detail'] = e.message

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
                'data': [DeploymentTargetItemResponseSchema().dump(deployment_target).data]
            }
        else:
            return_code = 404
            result = {
                'status': 'ERROR',
                'message': gettext('%s not found (id=%s)', self.human_name,
                                   deployment_target_id)
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
                                   deployment_target_id)
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
                                '%s (id=%s) was updated with success!',
                                self.human_name,
                                deployment_target_id),
                            'data': [response_schema.dump(deployment_target).data]
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
                                       deployment_target_id),
                    'errors': form.errors
                }
        return result, return_code
