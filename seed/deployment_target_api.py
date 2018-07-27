# -*- coding: utf-8 -*-}
from app_auth import requires_auth
from flask import request, current_app
from flask_restful import Resource
from schema import *


class DeploymentTargetListApi(Resource):
    """ REST API for listing class DeploymentTarget """

    @staticmethod
    @requires_auth
    def get():
        if request.args.get('fields'):
            only = [f.strip() for f in
                    request.args.get('fields').split(',')]
        else:
            only = ('id', 'name') if request.args.get('simple', 'false') == 'true' else None
        enabled_filter = request.args.get('enabled')
        if enabled_filter:
            deployment_targets = DeploymentTarget.query.filter(
                DeploymentTarget.enabled == (enabled_filter != 'false'))
        else:
            deployment_targets = DeploymentTarget.query.all()

        return DeploymentTargetListResponseSchema(
            many=True, only=only).dump(deployment_targets).data

    @staticmethod
    @requires_auth
    def post():
        result, result_code = dict(
            status="ERROR", message="Missing json in the request body"), 401
        if request.json is not None:
            request_schema = DeploymentTargetCreateRequestSchema()
            response_schema = DeploymentTargetItemResponseSchema()
            form = request_schema.load(request.json)
            if form.errors:
                result, result_code = dict(
                    status="ERROR", message="Validation error",
                    errors=form.errors), 401
            else:
                try:
                    deployment_target = form.data
                    db.session.add(deployment_target)
                    db.session.commit()
                    result, result_code = response_schema.dump(
                        deployment_target).data, 200
                except Exception, e:
                    result, result_code = dict(status="ERROR",
                                               message="Internal error"), 500
                    if current_app.debug:
                        result['debug_detail'] = e.message
                    db.session.rollback()

        return result, result_code


class DeploymentTargetDetailApi(Resource):
    """ REST API for a single instance of class DeploymentTarget """

    @staticmethod
    @requires_auth
    def get(deployment_target_id):
        deployment_target = DeploymentTarget.query.get(deployment_target_id)
        if deployment_target is not None:
            return DeploymentTargetItemResponseSchema().dump(deployment_target).data
        else:
            return dict(status="ERROR", message="Not found"), 404

    @staticmethod
    @requires_auth
    def delete(deployment_target_id):
        result, result_code = dict(status="ERROR", message="Not found"), 404

        deployment_target = DeploymentTarget.query.get(deployment_target_id)
        if deployment_target is not None:
            try:
                db.session.delete(deployment_target)
                db.session.commit()
                result, result_code = dict(status="OK", message="Deleted"), 200
            except Exception, e:
                result, result_code = dict(status="ERROR",
                                           message="Internal error"), 500
                if current_app.debug:
                    result['debug_detail'] = e.message
                db.session.rollback()
        return result, result_code

    @staticmethod
    @requires_auth
    def patch(deployment_target_id):
        result = dict(status="ERROR", message="Insufficient data")
        result_code = 404

        if request.json:
            request_schema = partial_schema_factory(DeploymentTargetCreateRequestSchema)
            # Ignore missing fields to allow partial updates
            form = request_schema.load(request.json, partial=True)
            response_schema = DeploymentTargetItemResponseSchema()
            if not form.errors:
                try:
                    form.data.id = deployment_target_id
                    deployment_target = db.session.merge(form.data)
                    db.session.commit()

                    if deployment_target is not None:
                        result, result_code = dict(
                            status="OK", message="Updated",
                            data=response_schema.dump(deployment_target).data), 200
                    else:
                        result = dict(status="ERROR", message="Not found")
                except Exception, e:
                    result, result_code = dict(status="ERROR",
                                               message="Internal error"), 500
                    if current_app.debug:
                        result['debug_detail'] = e.message
                    db.session.rollback()
            else:
                result = dict(status="ERROR", message="Invalid data",
                            errors=form.errors)
        return result, result_code

