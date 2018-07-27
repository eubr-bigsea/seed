# -*- coding: utf-8 -*-
import datetime
import json
from copy import deepcopy
from marshmallow import Schema, fields, post_load
from marshmallow.validate import OneOf
from seed.models import *


def partial_schema_factory(schema_cls):
    schema = schema_cls(partial=True)
    for field_name, field in schema.fields.items():
        if isinstance(field, fields.Nested):
            new_field = deepcopy(field)
            new_field.schema.partial = True
            schema.fields[field_name] = new_field
    return schema


def load_json(str_value):
    try:
        return json.loads(str_value)
    except BaseException:
        return "Error loading JSON"


# region Protected\s*
# endregion\w*


class DeploymentCreateRequestSchema(Schema):
    """ JSON serialization schema """
    description = fields.String(required=True)
    workflow_id = fields.Integer(required=True)
    user_id = fields.Integer(required=True)
    user_login = fields.String(required=True)
    user_name = fields.String(required=True)
    enabled = fields.Boolean(required=True)
    current_status = fields.String(required=True,
                                   validate=[OneOf(DeploymentStatus.__dict__.keys())])
    target = fields.Nested(
        'seed.schema.DeploymentTargetCreateRequestSchema',
        required=True)

    # noinspection PyUnresolvedReferences
    @post_load
    def make_object(self, data):
        """ Deserialize data into an instance of Deployment"""
        return Deployment(**data)

    class Meta:
        ordered = True


class DeploymentListResponseSchema(Schema):
    """ JSON serialization schema """
    id = fields.Integer(required=True)
    description = fields.String(required=True)
    workflow_id = fields.Integer(required=True)
    user_id = fields.Integer(required=True)
    user_login = fields.String(required=True)
    user_name = fields.String(required=True)
    enabled = fields.Boolean(required=True)
    current_status = fields.String(required=True,
                                   validate=[OneOf(DeploymentStatus.__dict__.keys())])
    target = fields.Nested(
        'seed.schema.DeploymentTargetListResponseSchema',
        required=True)

    # noinspection PyUnresolvedReferences
    @post_load
    def make_object(self, data):
        """ Deserialize data into an instance of Deployment"""
        return Deployment(**data)

    class Meta:
        ordered = True


class DeploymentItemResponseSchema(Schema):
    """ JSON serialization schema """
    id = fields.Integer(required=True)
    description = fields.String(required=True)
    workflow_id = fields.Integer(required=True)
    user_id = fields.Integer(required=True)
    user_login = fields.String(required=True)
    user_name = fields.String(required=True)
    enabled = fields.Boolean(required=True)
    current_status = fields.String(required=True,
                                   validate=[OneOf(DeploymentStatus.__dict__.keys())])
    target = fields.Nested(
        'seed.schema.DeploymentTargetItemResponseSchema',
        required=True)

    # noinspection PyUnresolvedReferences
    @post_load
    def make_object(self, data):
        """ Deserialize data into an instance of Deployment"""
        return Deployment(**data)

    class Meta:
        ordered = True


class DeploymentCreateRequestSchema(Schema):
    """ JSON serialization schema """
    id = fields.Integer(required=True)
    description = fields.String(required=True)
    workflow_id = fields.Integer(required=True)
    user_id = fields.Integer(required=True)
    user_login = fields.String(required=True)
    user_name = fields.String(required=True)
    enabled = fields.Boolean(required=True)
    current_status = fields.String(required=True,
                                   validate=[OneOf(DeploymentStatus.__dict__.keys())])
    target = fields.Nested(
        'seed.schema.DeploymentTargetCreateRequestSchema',
        required=True)

    # noinspection PyUnresolvedReferences
    @post_load
    def make_object(self, data):
        """ Deserialize data into an instance of Deployment"""
        return Deployment(**data)

    class Meta:
        ordered = True


class DeploymentItemResponseSchema(Schema):
    """ JSON serialization schema """
    id = fields.Integer(required=True)
    description = fields.String(required=True)
    workflow_id = fields.Integer(required=True)
    user_id = fields.Integer(required=True)
    user_login = fields.String(required=True)
    user_name = fields.String(required=True)
    enabled = fields.Boolean(required=True)
    current_status = fields.String(required=True,
                                   validate=[OneOf(DeploymentStatus.__dict__.keys())])
    target = fields.Nested(
        'seed.schema.DeploymentTargetItemResponseSchema',
        required=True)

    # noinspection PyUnresolvedReferences
    @post_load
    def make_object(self, data):
        """ Deserialize data into an instance of Deployment"""
        return Deployment(**data)

    class Meta:
        ordered = True


class DeploymentListResponseSchema(Schema):
    """ JSON serialization schema """
    id = fields.Integer(required=True)
    description = fields.String(required=True)
    workflow_id = fields.Integer(required=True)
    user_id = fields.Integer(required=True)
    user_login = fields.String(required=True)
    user_name = fields.String(required=True)
    enabled = fields.Boolean(required=True)
    current_status = fields.String(required=True,
                                   validate=[OneOf(DeploymentStatus.__dict__.keys())])
    target = fields.Nested(
        'seed.schema.DeploymentTargetListResponseSchema',
        required=True)

    # noinspection PyUnresolvedReferences
    @post_load
    def make_object(self, data):
        """ Deserialize data into an instance of Deployment"""
        return Deployment(**data)

    class Meta:
        ordered = True

