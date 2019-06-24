# -*- coding: utf-8 -*-
import datetime
import json
from copy import deepcopy
from marshmallow import Schema, fields, post_load
from marshmallow.validate import OneOf
from seed.models import *


def partial_schema_factory(schema_cls):
    schema = schema_cls(partial=True)
    for field_name, field in list(schema.fields.items()):
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


# region Protected
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


class DeploymentCreateRequestSchema(Schema):
    """ JSON serialization schema """
    description = fields.String(required=False, allow_none=True)
    created = fields.DateTime(required=True)
    updated = fields.DateTime(required=True)
    command = fields.String(required=False, allow_none=True)
    workflow_name = fields.String(required=True)
    workflow_id = fields.Integer(required=True)
    job_id = fields.Integer(required=False, allow_none=True)
    user_id = fields.Integer(required=True)
    user_login = fields.String(required=True)
    user_name = fields.String(required=True)
    enabled = fields.Boolean(required=True, missing=False)
    current_status = fields.String(required=True, missing=DeploymentStatus.PENDING,
                                   validate=[OneOf(list(DeploymentStatus.__dict__.keys()))])
    attempts = fields.Integer(required=True, missing=0)
    entry_point = fields.String(required=False, allow_none=True)
    target_id = fields.Integer(required=True)
    image_id = fields.Integer(required=True)

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
    description = fields.String(required=False, allow_none=True)
    created = fields.DateTime(required=True)
    updated = fields.DateTime(required=True)
    command = fields.String(required=False, allow_none=True)
    job_id = fields.Integer(required=False, allow_none=True)
    enabled = fields.Boolean(required=True, missing=False)
    current_status = fields.String(required=True, missing=DeploymentStatus.PENDING,
                                   validate=[OneOf(list(DeploymentStatus.__dict__.keys()))])
    attempts = fields.Integer(required=True, missing=0)
    log = fields.String(required=False, allow_none=True)
    entry_point = fields.String(required=False, allow_none=True)
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
    def make_object(self, data):
        """ Deserialize data into an instance of Deployment"""
        return Deployment(**data)

    class Meta:
        ordered = True


class DeploymentItemResponseSchema(Schema):
    """ JSON serialization schema """
    id = fields.Integer(required=True)
    description = fields.String(required=False, allow_none=True)
    created = fields.DateTime(required=True)
    updated = fields.DateTime(required=True)
    command = fields.String(required=False, allow_none=True)
    enabled = fields.Boolean(required=True, missing=False)
    current_status = fields.String(required=True, missing=DeploymentStatus.PENDING,
                                   validate=[OneOf(list(DeploymentStatus.__dict__.keys()))])
    attempts = fields.Integer(required=True, missing=0)
    log = fields.String(required=False, allow_none=True)
    entry_point = fields.String(required=False, allow_none=True)
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


class DeploymentLogCreateRequestSchema(Schema):
    """ JSON serialization schema """
    date = fields.DateTime(required=True, missing=datetime.datetime.utcnow)
    status = fields.String(required=True,
                           validate=[OneOf(list(DeploymentStatus.__dict__.keys()))])
    log = fields.String(required=True)

    # noinspection PyUnresolvedReferences
    @post_load
    def make_object(self, data):
        """ Deserialize data into an instance of DeploymentLog"""
        return DeploymentLog(**data)

    class Meta:
        ordered = True


class DeploymentLogListResponseSchema(Schema):
    """ JSON serialization schema """
    id = fields.Integer(required=True)
    date = fields.DateTime(required=True, missing=datetime.datetime.utcnow)
    status = fields.String(required=True,
                           validate=[OneOf(list(DeploymentStatus.__dict__.keys()))])
    log = fields.String(required=True)

    # noinspection PyUnresolvedReferences
    @post_load
    def make_object(self, data):
        """ Deserialize data into an instance of DeploymentLog"""
        return DeploymentLog(**data)

    class Meta:
        ordered = True


class DeploymentLogItemResponseSchema(Schema):
    """ JSON serialization schema """
    id = fields.Integer(required=True)
    date = fields.DateTime(required=True, missing=datetime.datetime.utcnow)
    status = fields.String(required=True,
                           validate=[OneOf(list(DeploymentStatus.__dict__.keys()))])
    log = fields.String(required=True)

    # noinspection PyUnresolvedReferences
    @post_load
    def make_object(self, data):
        """ Deserialize data into an instance of DeploymentLog"""
        return DeploymentLog(**data)

    class Meta:
        ordered = True


class DeploymentMetricCreateRequestSchema(Schema):
    """ JSON serialization schema """
    name = fields.String(required=True)
    parameters = fields.String(required=True)
    enabled = fields.Boolean(required=True)
    user_id = fields.Integer(required=True)
    user_login = fields.String(required=True)

    # noinspection PyUnresolvedReferences
    @post_load
    def make_object(self, data):
        """ Deserialize data into an instance of DeploymentMetric"""
        return DeploymentMetric(**data)

    class Meta:
        ordered = True


class DeploymentMetricListResponseSchema(Schema):
    """ JSON serialization schema """
    id = fields.Integer(required=True)
    name = fields.String(required=True)
    parameters = fields.String(required=True)
    enabled = fields.Boolean(required=True)
    user_id = fields.Integer(required=True)
    user_login = fields.String(required=True)

    # noinspection PyUnresolvedReferences
    @post_load
    def make_object(self, data):
        """ Deserialize data into an instance of DeploymentMetric"""
        return DeploymentMetric(**data)

    class Meta:
        ordered = True


class DeploymentMetricItemResponseSchema(Schema):
    """ JSON serialization schema """
    id = fields.Integer(required=True)
    name = fields.String(required=True)
    parameters = fields.String(required=True)
    enabled = fields.Boolean(required=True)
    user_id = fields.Integer(required=True)
    user_login = fields.String(required=True)

    # noinspection PyUnresolvedReferences
    @post_load
    def make_object(self, data):
        """ Deserialize data into an instance of DeploymentMetric"""
        return DeploymentMetric(**data)

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
                                validate=[OneOf(list(DeploymentType.__dict__.keys()))])
    descriptor = fields.String(required=False, allow_none=True)

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
                                validate=[OneOf(list(DeploymentType.__dict__.keys()))])
    descriptor = fields.String(required=False, allow_none=True)

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
                                validate=[OneOf(list(DeploymentType.__dict__.keys()))])
    descriptor = fields.String(required=False, allow_none=True)

    # noinspection PyUnresolvedReferences
    @post_load
    def make_object(self, data):
        """ Deserialize data into an instance of DeploymentTarget"""
        return DeploymentTarget(**data)

    class Meta:
        ordered = True


class TraceabilityCreateRequestSchema(Schema):
    """ JSON serialization schema """
    source_id = fields.Integer(required=True)
    source_type = fields.String(required=True,
                                validate=[OneOf(list(AuditableType.__dict__.keys()))])
    target_id = fields.Integer(required=True)
    target_type = fields.String(required=True,
                                validate=[OneOf(list(AuditableType.__dict__.keys()))])
    created = fields.DateTime(required=True)
    user_id = fields.Integer(required=True)
    user_login = fields.String(required=True)
    user_name = fields.String(required=True)
    context = fields.String(required=True)
    module = fields.String(required=True,
                           validate=[OneOf(list(ModuleType.__dict__.keys()))])
    action = fields.String(required=True,
                           validate=[OneOf(list(ActionType.__dict__.keys()))])
    job_id = fields.Integer(required=False, allow_none=True)
    workflow_id = fields.Integer(required=False, allow_none=True)
    workflow_name = fields.String(required=False, allow_none=True)
    task_id = fields.String(required=False, allow_none=True)
    task_name = fields.String(required=False, allow_none=True)
    task_type = fields.String(required=False, allow_none=True)
    risk_score = fields.Float(required=False, allow_none=True)
    platform_id = fields.Integer(required=False, allow_none=True)

    # noinspection PyUnresolvedReferences
    @post_load
    def make_object(self, data):
        """ Deserialize data into an instance of Traceability"""
        return Traceability(**data)

    class Meta:
        ordered = True


class TraceabilityListResponseSchema(Schema):
    """ JSON serialization schema """
    id = fields.Integer(required=True)
    source_id = fields.Integer(required=True)
    source_type = fields.String(required=True,
                                validate=[OneOf(list(AuditableType.__dict__.keys()))])
    target_id = fields.Integer(required=True)
    target_type = fields.String(required=True,
                                validate=[OneOf(list(AuditableType.__dict__.keys()))])
    created = fields.DateTime(required=True)
    user_id = fields.Integer(required=True)
    user_login = fields.String(required=True)
    user_name = fields.String(required=True)
    context = fields.String(required=True)
    module = fields.String(required=True,
                           validate=[OneOf(list(ModuleType.__dict__.keys()))])
    action = fields.String(required=True,
                           validate=[OneOf(list(ActionType.__dict__.keys()))])
    job_id = fields.Integer(required=False, allow_none=True)
    workflow_id = fields.Integer(required=False, allow_none=True)
    workflow_name = fields.String(required=False, allow_none=True)
    task_id = fields.String(required=False, allow_none=True)
    task_name = fields.String(required=False, allow_none=True)
    task_type = fields.String(required=False, allow_none=True)
    risk_score = fields.Float(required=False, allow_none=True)
    platform_id = fields.Integer(required=False, allow_none=True)

    # noinspection PyUnresolvedReferences
    @post_load
    def make_object(self, data):
        """ Deserialize data into an instance of Traceability"""
        return Traceability(**data)

    class Meta:
        ordered = True


class TraceabilityItemResponseSchema(Schema):
    """ JSON serialization schema """
    id = fields.Integer(required=True)
    source_id = fields.Integer(required=True)
    source_type = fields.String(required=True,
                                validate=[OneOf(list(AuditableType.__dict__.keys()))])
    target_id = fields.Integer(required=True)
    target_type = fields.String(required=True,
                                validate=[OneOf(list(AuditableType.__dict__.keys()))])
    created = fields.DateTime(required=True)
    user_id = fields.Integer(required=True)
    user_login = fields.String(required=True)
    user_name = fields.String(required=True)
    context = fields.String(required=True)
    module = fields.String(required=True,
                           validate=[OneOf(list(ModuleType.__dict__.keys()))])
    action = fields.String(required=True,
                           validate=[OneOf(list(ActionType.__dict__.keys()))])
    job_id = fields.Integer(required=False, allow_none=True)
    workflow_id = fields.Integer(required=False, allow_none=True)
    workflow_name = fields.String(required=False, allow_none=True)
    task_id = fields.String(required=False, allow_none=True)
    task_name = fields.String(required=False, allow_none=True)
    task_type = fields.String(required=False, allow_none=True)
    risk_score = fields.Float(required=False, allow_none=True)
    platform_id = fields.Integer(required=False, allow_none=True)

    # noinspection PyUnresolvedReferences
    @post_load
    def make_object(self, data):
        """ Deserialize data into an instance of Traceability"""
        return Traceability(**data)

    class Meta:
        ordered = True


class TraceabilityCreateRequestSchema(Schema):
    """ JSON serialization schema """
    id = fields.Integer(required=True)
    source_id = fields.Integer(required=True)
    source_type = fields.String(required=True,
                                validate=[OneOf(list(AuditableType.__dict__.keys()))])
    target_id = fields.Integer(required=True)
    target_type = fields.String(required=True,
                                validate=[OneOf(list(AuditableType.__dict__.keys()))])
    created = fields.DateTime(required=True)
    user_id = fields.Integer(required=True)
    user_login = fields.String(required=True)
    user_name = fields.String(required=True)
    context = fields.String(required=True)
    module = fields.String(required=True,
                           validate=[OneOf(list(ModuleType.__dict__.keys()))])
    action = fields.String(required=True,
                           validate=[OneOf(list(ActionType.__dict__.keys()))])
    job_id = fields.Integer(required=False, allow_none=True)
    workflow_id = fields.Integer(required=False, allow_none=True)
    workflow_name = fields.String(required=False, allow_none=True)
    task_id = fields.String(required=False, allow_none=True)
    task_name = fields.String(required=False, allow_none=True)
    task_type = fields.String(required=False, allow_none=True)
    risk_score = fields.Float(required=False, allow_none=True)
    platform_id = fields.Integer(required=False, allow_none=True)

    # noinspection PyUnresolvedReferences
    @post_load
    def make_object(self, data):
        """ Deserialize data into an instance of Traceability"""
        return Traceability(**data)

    class Meta:
        ordered = True

