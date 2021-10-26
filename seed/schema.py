# -*- coding: utf-8 -*-
import datetime
import json
from copy import deepcopy
from marshmallow import Schema, fields, post_load, post_dump, EXCLUDE, INCLUDE
from marshmallow.validate import OneOf
from flask_babel import gettext
from seed.models import *

def partial_schema_factory(schema_cls):
    schema = schema_cls(partial=True)
    for field_name, field in list(schema.fields.items()):
        if isinstance(field, fields.Nested):
            new_field = deepcopy(field)
            new_field.schema.partial = True
            schema.fields[field_name] = new_field
    return schema


def translate_validation(validation_errors):
    for field, errors in list(validation_errors.items()):
        if isinstance(errors, dict):
            validation_errors[field] = translate_validation(errors)
        else:
            validation_errors[field] = [gettext(error) for error in errors]
        return validation_errors


def load_json(str_value):
    try:
        return json.loads(str_value)
    except BaseException:
        return None


# region Protected
# endregion

class BaseSchema(Schema):
    @post_dump
    def remove_skip_values(self, data, **kwargs):
        return {
            key: value for key, value in data.items()
            if value is not None  # Empty lists must be kept!
        }


class ClientCreateRequestSchema(BaseSchema):
    """ JSON serialization schema """
    name = fields.String(required=True)
    enabled = fields.Boolean(required=True)
    token = fields.String(required=True)
    deployment_id = fields.Integer(required=True)

    # noinspection PyUnresolvedReferences
    @post_load
    def make_object(self, data, **kwargs):
        """ Deserialize data into an instance of Client"""
        return Client(**data)

    class Meta:
        ordered = True
        unknown = EXCLUDE


class ClientListResponseSchema(BaseSchema):
    """ JSON serialization schema """
    id = fields.Integer(required=True)
    name = fields.String(required=True)
    enabled = fields.Boolean(required=True)
    token = fields.String(required=True)

    # noinspection PyUnresolvedReferences
    @post_load
    def make_object(self, data, **kwargs):
        """ Deserialize data into an instance of Client"""
        return Client(**data)

    class Meta:
        ordered = True
        unknown = EXCLUDE


class ClientItemResponseSchema(BaseSchema):
    """ JSON serialization schema """
    id = fields.Integer(required=True)
    name = fields.String(required=True)
    enabled = fields.Boolean(required=True)
    token = fields.String(required=True)
    deployment_id = fields.Integer(required=True)

    # noinspection PyUnresolvedReferences
    @post_load
    def make_object(self, data, **kwargs):
        """ Deserialize data into an instance of Client"""
        return Client(**data)

    class Meta:
        ordered = True
        unknown = EXCLUDE


class DeploymentCreateRequestSchema(BaseSchema):
    """ JSON serialization schema """
    description = fields.String(required=False, allow_none=True)
    created = fields.DateTime(required=False, allow_none=True)
    updated = fields.DateTime(required=False, allow_none=True)
    command = fields.String(required=False, allow_none=True)
    workflow_name = fields.String(required=True)
    workflow_id = fields.Integer(required=False, allow_none=True)
    job_id = fields.Integer(required=False, allow_none=True)
    model_id = fields.Integer(required=False, allow_none=True)
    user_id = fields.Integer(required=True)
    user_login = fields.String(required=True)
    user_name = fields.String(required=True)
    enabled = fields.Boolean(
        required=False,
        allow_none=True,
        missing=False,
        default=False)
    current_status = fields.String(required=False, allow_none=True, missing=DeploymentStatus.PENDING, default=DeploymentStatus.PENDING,
                                   validate=[OneOf(list(DeploymentStatus.__dict__.keys()))])
    type = fields.String(required=False, allow_none=True, missing=DeploymentType.MODEL, default=DeploymentType.MODEL,
                         validate=[OneOf(list(DeploymentType.__dict__.keys()))])
    attempts = fields.Integer(
        required=False,
        allow_none=True,
        missing=0,
        default=0)
    entry_point = fields.String(required=False, allow_none=True)
    replicas = fields.Integer(
        required=False,
        allow_none=True,
        missing=1,
        default=1)
    request_memory = fields.String(
        required=False,
        allow_none=True,
        missing='128M',
        default='128M')
    limit_memory = fields.String(required=False, allow_none=True)
    request_cpu = fields.Decimal(
        required=False,
        allow_none=True,
        missing=0.5,
        default=0.5)
    limit_cpu = fields.Decimal(required=False, allow_none=True)
    extra_parameters = fields.String(required=False, allow_none=True)
    input_spec = fields.String(required=False, allow_none=True)
    output_spec = fields.String(required=False, allow_none=True)
    target_id = fields.Integer(required=True)
    image_id = fields.Integer(required=True)

    # noinspection PyUnresolvedReferences
    @post_load
    def make_object(self, data, **kwargs):
        """ Deserialize data into an instance of Deployment"""
        return Deployment(**data)

    class Meta:
        ordered = True
        unknown = EXCLUDE


class DeploymentListResponseSchema(BaseSchema):
    """ JSON serialization schema """
    id = fields.Integer(required=True)
    description = fields.String(required=False, allow_none=True)
    created = fields.DateTime(required=False, allow_none=True)
    updated = fields.DateTime(required=False, allow_none=True)
    command = fields.String(required=False, allow_none=True)
    job_id = fields.Integer(required=False, allow_none=True)
    model_id = fields.Integer(required=False, allow_none=True)
    enabled = fields.Boolean(
        required=False,
        allow_none=True,
        missing=False,
        default=False)
    current_status = fields.String(required=False, allow_none=True, missing=DeploymentStatus.PENDING, default=DeploymentStatus.PENDING,
                                   validate=[OneOf(list(DeploymentStatus.__dict__.keys()))])
    type = fields.String(required=False, allow_none=True, missing=DeploymentType.MODEL, default=DeploymentType.MODEL,
                         validate=[OneOf(list(DeploymentType.__dict__.keys()))])
    attempts = fields.Integer(
        required=False,
        allow_none=True,
        missing=0,
        default=0)
    log = fields.String(required=False, allow_none=True)
    entry_point = fields.String(required=False, allow_none=True)
    replicas = fields.Integer(
        required=False,
        allow_none=True,
        missing=1,
        default=1)
    request_memory = fields.String(
        required=False,
        allow_none=True,
        missing='128M',
        default='128M')
    limit_memory = fields.String(required=False, allow_none=True)
    request_cpu = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        missing=0.5,
        default=0.5)
    limit_cpu = fields.Decimal(required=False, allow_none=True, as_string=True)
    extra_parameters = fields.String(required=False, allow_none=True)
    input_spec = fields.String(required=False, allow_none=True)
    output_spec = fields.String(required=False, allow_none=True)
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
    workflow = fields.Function(
        lambda x: {
            "id": x.workflow_id,
            "name": x.workflow_name})
    job = fields.Function(lambda x: {"id": x.job_id})

    # noinspection PyUnresolvedReferences
    @post_load
    def make_object(self, data, **kwargs):
        """ Deserialize data into an instance of Deployment"""
        return Deployment(**data)

    class Meta:
        ordered = True
        unknown = EXCLUDE


class DeploymentItemResponseSchema(BaseSchema):
    """ JSON serialization schema """
    id = fields.Integer(required=True)
    description = fields.String(required=False, allow_none=True)
    created = fields.DateTime(required=False, allow_none=True)
    updated = fields.DateTime(required=False, allow_none=True)
    command = fields.String(required=False, allow_none=True)
    model_id = fields.Integer(required=False, allow_none=True)
    enabled = fields.Boolean(
        required=False,
        allow_none=True,
        missing=False,
        default=False)
    current_status = fields.String(required=False, allow_none=True, missing=DeploymentStatus.PENDING, default=DeploymentStatus.PENDING,
                                   validate=[OneOf(list(DeploymentStatus.__dict__.keys()))])
    type = fields.String(required=False, allow_none=True, missing=DeploymentType.MODEL, default=DeploymentType.MODEL,
                         validate=[OneOf(list(DeploymentType.__dict__.keys()))])
    attempts = fields.Integer(
        required=False,
        allow_none=True,
        missing=0,
        default=0)
    log = fields.String(required=False, allow_none=True)
    entry_point = fields.String(required=False, allow_none=True)
    replicas = fields.Integer(
        required=False,
        allow_none=True,
        missing=1,
        default=1)
    request_memory = fields.String(
        required=False,
        allow_none=True,
        missing='128M',
        default='128M')
    limit_memory = fields.String(required=False, allow_none=True)
    request_cpu = fields.Decimal(
        required=False,
        allow_none=True,
        as_string=True,
        missing=0.5,
        default=0.5)
    limit_cpu = fields.Decimal(required=False, allow_none=True, as_string=True)
    extra_parameters = fields.String(required=False, allow_none=True)
    input_spec = fields.String(required=False, allow_none=True)
    output_spec = fields.String(required=False, allow_none=True)
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
    workflow = fields.Function(
        lambda x: {
            "id": x.workflow_id,
            "name": x.workflow_name})
    job = fields.Function(lambda x: {"id": x.job_id})

    # noinspection PyUnresolvedReferences
    @post_load
    def make_object(self, data, **kwargs):
        """ Deserialize data into an instance of Deployment"""
        return Deployment(**data)

    class Meta:
        ordered = True
        unknown = EXCLUDE


class DeploymentImageListResponseSchema(BaseSchema):
    """ JSON serialization schema """
    id = fields.Integer(required=True)
    name = fields.String(required=True)
    tag = fields.String(required=True)
    enabled = fields.Boolean(required=True)

    # noinspection PyUnresolvedReferences
    @post_load
    def make_object(self, data, **kwargs):
        """ Deserialize data into an instance of DeploymentImage"""
        return DeploymentImage(**data)

    class Meta:
        ordered = True
        unknown = EXCLUDE


class DeploymentImageItemResponseSchema(BaseSchema):
    """ JSON serialization schema """
    id = fields.Integer(required=True)
    name = fields.String(required=True)
    tag = fields.String(required=True)
    enabled = fields.Boolean(required=True)

    # noinspection PyUnresolvedReferences
    @post_load
    def make_object(self, data, **kwargs):
        """ Deserialize data into an instance of DeploymentImage"""
        return DeploymentImage(**data)

    class Meta:
        ordered = True
        unknown = EXCLUDE


class DeploymentImageCreateRequestSchema(BaseSchema):
    """ JSON serialization schema """
    id = fields.Integer(required=True)
    name = fields.String(required=True)
    tag = fields.String(required=True)
    enabled = fields.Boolean(required=True)

    # noinspection PyUnresolvedReferences
    @post_load
    def make_object(self, data, **kwargs):
        """ Deserialize data into an instance of DeploymentImage"""
        return DeploymentImage(**data)

    class Meta:
        ordered = True
        unknown = EXCLUDE


class DeploymentLogCreateRequestSchema(BaseSchema):
    """ JSON serialization schema """
    date = fields.DateTime(
        required=False,
        allow_none=True,
        missing=datetime.datetime.utcnow,
        default=datetime.datetime.utcnow)
    status = fields.String(required=True,
                           validate=[OneOf(list(DeploymentStatus.__dict__.keys()))])
    log = fields.String(required=True)
    deployment_id = fields.Integer(required=True)

    # noinspection PyUnresolvedReferences
    @post_load
    def make_object(self, data, **kwargs):
        """ Deserialize data into an instance of DeploymentLog"""
        return DeploymentLog(**data)

    class Meta:
        ordered = True
        unknown = EXCLUDE


class DeploymentLogListResponseSchema(BaseSchema):
    """ JSON serialization schema """
    id = fields.Integer(required=True)
    date = fields.DateTime(
        required=False,
        allow_none=True,
        missing=datetime.datetime.utcnow,
        default=datetime.datetime.utcnow)
    status = fields.String(required=True,
                           validate=[OneOf(list(DeploymentStatus.__dict__.keys()))])
    log = fields.String(required=True)

    # noinspection PyUnresolvedReferences
    @post_load
    def make_object(self, data, **kwargs):
        """ Deserialize data into an instance of DeploymentLog"""
        return DeploymentLog(**data)

    class Meta:
        ordered = True
        unknown = EXCLUDE


class DeploymentLogItemResponseSchema(BaseSchema):
    """ JSON serialization schema """
    id = fields.Integer(required=True)
    date = fields.DateTime(
        required=False,
        allow_none=True,
        missing=datetime.datetime.utcnow,
        default=datetime.datetime.utcnow)
    status = fields.String(required=True,
                           validate=[OneOf(list(DeploymentStatus.__dict__.keys()))])
    log = fields.String(required=True)

    # noinspection PyUnresolvedReferences
    @post_load
    def make_object(self, data, **kwargs):
        """ Deserialize data into an instance of DeploymentLog"""
        return DeploymentLog(**data)

    class Meta:
        ordered = True
        unknown = EXCLUDE


class DeploymentMetricCreateRequestSchema(BaseSchema):
    """ JSON serialization schema """
    name = fields.String(required=True)
    parameters = fields.String(required=True)
    enabled = fields.Boolean(required=True)
    user_id = fields.Integer(required=True)
    user_login = fields.String(required=True)

    # noinspection PyUnresolvedReferences
    @post_load
    def make_object(self, data, **kwargs):
        """ Deserialize data into an instance of DeploymentMetric"""
        return DeploymentMetric(**data)

    class Meta:
        ordered = True
        unknown = EXCLUDE


class DeploymentMetricListResponseSchema(BaseSchema):
    """ JSON serialization schema """
    id = fields.Integer(required=True)
    name = fields.String(required=True)
    parameters = fields.String(required=True)
    enabled = fields.Boolean(required=True)
    user_id = fields.Integer(required=True)
    user_login = fields.String(required=True)

    # noinspection PyUnresolvedReferences
    @post_load
    def make_object(self, data, **kwargs):
        """ Deserialize data into an instance of DeploymentMetric"""
        return DeploymentMetric(**data)

    class Meta:
        ordered = True
        unknown = EXCLUDE


class DeploymentMetricItemResponseSchema(BaseSchema):
    """ JSON serialization schema """
    id = fields.Integer(required=True)
    name = fields.String(required=True)
    parameters = fields.String(required=True)
    enabled = fields.Boolean(required=True)
    user_id = fields.Integer(required=True)
    user_login = fields.String(required=True)

    # noinspection PyUnresolvedReferences
    @post_load
    def make_object(self, data, **kwargs):
        """ Deserialize data into an instance of DeploymentMetric"""
        return DeploymentMetric(**data)

    class Meta:
        ordered = True
        unknown = EXCLUDE


class DeploymentTargetCreateRequestSchema(BaseSchema):
    """ JSON serialization schema """
    name = fields.String(required=True)
    description = fields.String(required=False, allow_none=True)
    url = fields.String(required=True)
    authentication_info = fields.String(required=False, allow_none=True)
    enabled = fields.Boolean(required=True)
    target_type = fields.String(required=True,
                                validate=[OneOf(list(DeploymentTypeTarget.__dict__.keys()))])
    descriptor = fields.String(required=False, allow_none=True)

    # noinspection PyUnresolvedReferences
    @post_load
    def make_object(self, data, **kwargs):
        """ Deserialize data into an instance of DeploymentTarget"""
        return DeploymentTarget(**data)

    class Meta:
        ordered = True
        unknown = EXCLUDE


class DeploymentTargetListResponseSchema(BaseSchema):
    """ JSON serialization schema """
    id = fields.Integer(required=True)
    name = fields.String(required=True)
    description = fields.String(required=False, allow_none=True)
    enabled = fields.Boolean(required=True)
    target_type = fields.String(required=True,
                                validate=[OneOf(list(DeploymentTypeTarget.__dict__.keys()))])
    descriptor = fields.String(required=False, allow_none=True)

    # noinspection PyUnresolvedReferences
    @post_load
    def make_object(self, data, **kwargs):
        """ Deserialize data into an instance of DeploymentTarget"""
        return DeploymentTarget(**data)

    class Meta:
        ordered = True
        unknown = EXCLUDE


class DeploymentTargetItemResponseSchema(BaseSchema):
    """ JSON serialization schema """
    id = fields.Integer(required=True)
    name = fields.String(required=True)
    description = fields.String(required=False, allow_none=True)
    url = fields.String(required=True)
    authentication_info = fields.String(required=False, allow_none=True)
    enabled = fields.Boolean(required=True)
    target_type = fields.String(required=True,
                                validate=[OneOf(list(DeploymentTypeTarget.__dict__.keys()))])
    descriptor = fields.String(required=False, allow_none=True)

    # noinspection PyUnresolvedReferences
    @post_load
    def make_object(self, data, **kwargs):
        """ Deserialize data into an instance of DeploymentTarget"""
        return DeploymentTarget(**data)

    class Meta:
        ordered = True
        unknown = EXCLUDE

