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
# endregion


class ClientCreateRequestSchema(Schema):
    """ JSON serialization schema """
    name = fields.String(required=True)
    enabled = fields.Boolean(required=True)
    token = fields.String(required=True)

    # noinspection PyUnresolvedReferences
    @post_load
    def make_object(self, data):
        """ Deserialize data into an instance of Client"""
        return Client(**data)

    class Meta:
        ordered = True


class ClientListResponseSchema(Schema):
    """ JSON serialization schema """
    id = fields.Integer(required=True)
    name = fields.String(required=True)
    enabled = fields.Boolean(required=True)
    token = fields.String(required=True)

    # noinspection PyUnresolvedReferences
    @post_load
    def make_object(self, data):
        """ Deserialize data into an instance of Client"""
        return Client(**data)

    class Meta:
        ordered = True


class ClientItemResponseSchema(Schema):
    """ JSON serialization schema """
    id = fields.Integer(required=True)
    name = fields.String(required=True)
    enabled = fields.Boolean(required=True)
    token = fields.String(required=True)

    # noinspection PyUnresolvedReferences
    @post_load
    def make_object(self, data):
        """ Deserialize data into an instance of Client"""
        return Client(**data)

    class Meta:
        ordered = True


class ClientCreateRequestSchema(Schema):
    """ JSON serialization schema """
    id = fields.Integer(required=True)
    name = fields.String(required=True)
    enabled = fields.Boolean(required=True)
    token = fields.String(required=True)
    deployment = fields.Nested(
        'seed.schema.DeploymentCreateRequestSchema',
        required=True)

    # noinspection PyUnresolvedReferences
    @post_load
    def make_object(self, data):
        """ Deserialize data into an instance of Client"""
        return Client(**data)

    class Meta:
        ordered = True


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
    attempts = fields.Integer(required=True)
    log = fields.String(required=False, allow_none=True)
    entry_point = fields.String(required=True)
    target = fields.Nested(
        'seed.schema.DeploymentTargetCreateRequestSchema',
        required=True)
    image = fields.Nested(
        'seed.schema.DeploymentImageCreateRequestSchema',
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
    enabled = fields.Boolean(required=True)
    current_status = fields.String(required=True,
                                   validate=[OneOf(DeploymentStatus.__dict__.keys())])
    attempts = fields.Integer(required=True)
    log = fields.String(required=False, allow_none=True)
    entry_point = fields.String(required=True)
    target = fields.Nested(
        'seed.schema.DeploymentTargetListResponseSchema',
        required=True)
    image = fields.Nested(
        'seed.schema.DeploymentImageListResponseSchema',
        required=True)
    user = fields.Function(
        lambda x: {
            "id": x.user_id,
            "name": x.user_name,
            "login": x.user_login})

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
    enabled = fields.Boolean(required=True)
    current_status = fields.String(required=True,
                                   validate=[OneOf(DeploymentStatus.__dict__.keys())])
    attempts = fields.Integer(required=True)
    log = fields.String(required=False, allow_none=True)
    entry_point = fields.String(required=True)
    target = fields.Nested(
        'seed.schema.DeploymentTargetItemResponseSchema',
        required=True)
    image = fields.Nested(
        'seed.schema.DeploymentImageItemResponseSchema',
        required=True)
    user = fields.Function(
        lambda x: {
            "id": x.user_id,
            "name": x.user_name,
            "login": x.user_login})

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
    attempts = fields.Integer(required=True)
    log = fields.String(required=False, allow_none=True)
    entry_point = fields.String(required=True)
    target = fields.Nested(
        'seed.schema.DeploymentTargetCreateRequestSchema',
        required=True)
    image = fields.Nested(
        'seed.schema.DeploymentImageCreateRequestSchema',
        required=True)

    # noinspection PyUnresolvedReferences
    @post_load
    def make_object(self, data):
        """ Deserialize data into an instance of Deployment"""
        return Deployment(**data)

    class Meta:
        ordered = True


class DeploymentImageCreateRequestSchema(Schema):
    """ JSON serialization schema """
    name = fields.String(required=True)
    tag = fields.String(required=True)
    enabled = fields.Boolean(required=True)

    # noinspection PyUnresolvedReferences
    @post_load
    def make_object(self, data):
        """ Deserialize data into an instance of DeploymentImage"""
        return DeploymentImage(**data)

    class Meta:
        ordered = True


class DeploymentImageListResponseSchema(Schema):
    """ JSON serialization schema """
    id = fields.Integer(required=True)
    name = fields.String(required=True)
    tag = fields.String(required=True)
    enabled = fields.Boolean(required=True)

    # noinspection PyUnresolvedReferences
    @post_load
    def make_object(self, data):
        """ Deserialize data into an instance of DeploymentImage"""
        return DeploymentImage(**data)

    class Meta:
        ordered = True


class DeploymentImageItemResponseSchema(Schema):
    """ JSON serialization schema """
    id = fields.Integer(required=True)
    name = fields.String(required=True)
    tag = fields.String(required=True)
    enabled = fields.Boolean(required=True)

    # noinspection PyUnresolvedReferences
    @post_load
    def make_object(self, data):
        """ Deserialize data into an instance of DeploymentImage"""
        return DeploymentImage(**data)

    class Meta:
        ordered = True


class DeploymentImageCreateRequestSchema(Schema):
    """ JSON serialization schema """
    id = fields.Integer(required=True)
    name = fields.String(required=True)
    tag = fields.String(required=True)
    enabled = fields.Boolean(required=True)

    # noinspection PyUnresolvedReferences
    @post_load
    def make_object(self, data):
        """ Deserialize data into an instance of DeploymentImage"""
        return DeploymentImage(**data)

    class Meta:
        ordered = True


class DeploymentTargetCreateRequestSchema(Schema):
    """ JSON serialization schema """
    name = fields.String(required=True)
    description = fields.String(required=False, allow_none=True)
    url = fields.String(required=True)
    authentication_info = fields.String(required=False, allow_none=True)
    enabled = fields.Boolean(required=True)
    target_type = fields.String(required=True,
                                validate=[OneOf(DeploymentType.__dict__.keys())])

    # noinspection PyUnresolvedReferences
    @post_load
    def make_object(self, data):
        """ Deserialize data into an instance of DeploymentTarget"""
        return DeploymentTarget(**data)

    class Meta:
        ordered = True


class DeploymentTargetListResponseSchema(Schema):
    """ JSON serialization schema """
    id = fields.Integer(required=True)
    name = fields.String(required=True)
    description = fields.String(required=False, allow_none=True)
    enabled = fields.Boolean(required=True)
    target_type = fields.String(required=True,
                                validate=[OneOf(DeploymentType.__dict__.keys())])

    # noinspection PyUnresolvedReferences
    @post_load
    def make_object(self, data):
        """ Deserialize data into an instance of DeploymentTarget"""
        return DeploymentTarget(**data)

    class Meta:
        ordered = True


class DeploymentTargetItemResponseSchema(Schema):
    """ JSON serialization schema """
    id = fields.Integer(required=True)
    name = fields.String(required=True)
    description = fields.String(required=False, allow_none=True)
    url = fields.String(required=True)
    authentication_info = fields.String(required=False, allow_none=True)
    enabled = fields.Boolean(required=True)
    target_type = fields.String(required=True,
                                validate=[OneOf(DeploymentType.__dict__.keys())])

    # noinspection PyUnresolvedReferences
    @post_load
    def make_object(self, data):
        """ Deserialize data into an instance of DeploymentTarget"""
        return DeploymentTarget(**data)

    class Meta:
        ordered = True


class DeploymentTargetCreateRequestSchema(Schema):
    """ JSON serialization schema """
    id = fields.Integer(required=True)
    name = fields.String(required=True)
    description = fields.String(required=False, allow_none=True)
    url = fields.String(required=True)
    authentication_info = fields.String(required=False, allow_none=True)
    enabled = fields.Boolean(required=True)
    target_type = fields.String(required=True,
                                validate=[OneOf(DeploymentType.__dict__.keys())])

    # noinspection PyUnresolvedReferences
    @post_load
    def make_object(self, data):
        """ Deserialize data into an instance of DeploymentTarget"""
        return DeploymentTarget(**data)

    class Meta:
        ordered = True

