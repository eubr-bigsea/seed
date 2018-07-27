# -*- coding: utf-8 -*-}
from app_auth import requires_auth
from flask import request, current_app
from flask_restful import Resource
from schema import *


class DeploymentListApi(Resource):
    """ REST API for listing class Deployment """

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
            deployments = Deployment.query.filter(
                Deployment.enabled == (enabled_filter != 'false'))
        else:
            deployments = Deployment.query.all()

        return DeploymentListResponseSchema(
            many=True, only=only).dump(deployments).data

    @staticmethod
    @requires_auth
    def post():
        result, result_code = dict(
            status="ERROR", message="Missing json in the request body"), 401
        if request.json is not None:
            request_schema = DeploymentCreateRequestSchema()
            response_schema = DeploymentItemResponseSchema()
            form = request_schema.load(request.json)
            if form.errors:
                result, result_code = dict(
                    status="ERROR", message="Validation error",
                    errors=form.errors), 401
            else:
                try:
                    deployment = form.data
                    db.session.add(deployment)
                    db.session.commit()
                    result, result_code = response_schema.dump(
                        deployment).data, 200
                except Exception, e:
                    result, result_code = dict(status="ERROR",
                                               message="Internal error"), 500
                    if current_app.debug:
                        result['debug_detail'] = e.message
                    db.session.rollback()

        return result, result_code


class DeploymentDetailApi(Resource):
    """ REST API for a single instance of class Deployment """

    @staticmethod
    @requires_auth
    def get(deployment_id):
        deployment = Deployment.query.get(deployment_id)
        if deployment is not None:
            return DeploymentItemResponseSchema().dump(deployment).data
        else:
            return dict(status="ERROR", message="Not found"), 404

    @staticmethod
    @requires_auth
    def delete(deployment_id):
        result, result_code = dict(status="ERROR", message="Not found"), 404

        deployment = Deployment.query.get(deployment_id)
        if deployment is not None:
            try:
                db.session.delete(deployment)
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
    def patch(deployment_id):
        result = dict(status="ERROR", message="Insufficient data")
        result_code = 404

        if request.json:
            request_schema = partial_schema_factory(DeploymentCreateRequestSchema)
            # Ignore missing fields to allow partial updates
            form = request_schema.load(request.json, partial=True)
            response_schema = DeploymentItemResponseSchema()
            if not form.errors:
                try:
                    form.data.id = deployment_id
                    deployment = db.session.merge(form.data)
                    db.session.commit()

                    if deployment is not None:
                        result, result_code = dict(
                            status="OK", message="Updated",
                            data=response_schema.dump(deployment).data), 200
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

