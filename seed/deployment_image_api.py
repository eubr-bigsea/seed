# -*- coding: utf-8 -*-}
from app_auth import requires_auth
from flask import request, current_app
from flask_restful import Resource

import logging
from schema import *
from flask_babel import gettext


log = logging.getLogger(__name__)


class DeploymentImageListApi(Resource):
    """ REST API for listing class DeploymentImage """

    def __init__(self):
        self.human_name = gettext('DeploymentImage')

    @requires_auth
    def get(self):
        if request.args.get('fields'):
            only = [f.strip() for f in
                    request.args.get('fields').split(',')]
        else:
            only = ('id', ) if request.args.get(
                'simple', 'false') == 'true' else None
        enabled_filter = request.args.get('enabled')
        if enabled_filter:
            deployment_images = DeploymentImage.query.filter(
                DeploymentImage.enabled == (enabled_filter != 'false'))
        else:
            deployment_images = DeploymentImage.query.all()

        if log.isEnabledFor(logging.DEBUG):
            log.debug(gettext('Listing %s'), self.human_name)
        return {
            'status': 'OK',
            'data': DeploymentImageListResponseSchema(
                    many=True, only=only).dump(deployment_images).data
        }

    @requires_auth
    def post(self):
        result = {'status': 'ERROR', 
                  'message': gettext("Missing json in the request body")}
        return_code = 400
        
        if request.json is not None:
            request_schema = DeploymentImageCreateRequestSchema()
            response_schema = DeploymentImageItemResponseSchema()
            form = request_schema.load(request.json)
            if form.errors:
                result = {'status': 'ERROR',
                          'message': gettext("Validation error"),
                          'errors': form.errors}
            else:
                try:
                    if log.isEnabledFor(logging.DEBUG):
                        log.debug(gettext('Adding %s'), self.human_name)
                    deployment_image = form.data
                    db.session.add(deployment_image)
                    db.session.commit()
                    result = response_schema.dump(deployment_image).data
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


class DeploymentImageDetailApi(Resource):
    """ REST API for a single instance of class DeploymentImage """
    def __init__(self):
        self.human_name = gettext('DeploymentImage')

    @requires_auth
    def get(self, deployment_image_id):

        if log.isEnabledFor(logging.DEBUG):
            log.debug(gettext('Retrieving %s (id=%s)'), self.human_name,
                      deployment_image_id)

        deployment_image = DeploymentImage.query.get(deployment_image_id)
        return_code = 200
        if deployment_image is not None:
            result = {
                'status': 'OK',
                'data': [DeploymentImageItemResponseSchema().dump(deployment_image).data]
            }
        else:
            return_code = 404
            result = {
                'status': 'ERROR',
                'message': gettext('%s not found (id=%s)', self.human_name,
                                   deployment_image_id)
            }

        return result, return_code

    @requires_auth
    def delete(self, deployment_image_id):
        return_code = 200
        if log.isEnabledFor(logging.DEBUG):
            log.debug(gettext('Deleting %s (id=%s)'), self.human_name,
                      deployment_image_id)
        deployment_image = DeploymentImage.query.get(deployment_image_id)
        if deployment_image is not None:
            try:
                db.session.delete(deployment_image)
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
                                   deployment_image_id)
            }
        return result, return_code

    @requires_auth
    def patch(self, deployment_image_id):
        result = {'status': 'ERROR', 'message': gettext('Insufficient data.')}
        return_code = 404

        if log.isEnabledFor(logging.DEBUG):
            log.debug(gettext('Updating %s (id=%s)'), self.human_name,
                      deployment_image_id)
        if request.json:
            request_schema = partial_schema_factory(
                DeploymentImageCreateRequestSchema)
            # Ignore missing fields to allow partial updates
            form = request_schema.load(request.json, partial=True)
            response_schema = DeploymentImageItemResponseSchema()
            if not form.errors:
                try:
                    form.data.id = deployment_image_id
                    deployment_image = db.session.merge(form.data)
                    db.session.commit()

                    if deployment_image is not None:
                        return_code = 200
                        result = {
                            'status': 'OK',
                            'message': gettext(
                                '%s (id=%s) was updated with success!',
                                self.human_name,
                                deployment_image_id),
                            'data': [response_schema.dump(deployment_image).data]
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
                                       deployment_image_id),
                    'errors': form.errors
                }
        return result, return_code
