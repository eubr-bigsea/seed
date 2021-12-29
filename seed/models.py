import datetime
import json
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Float, \
    Enum, DateTime, Numeric, Text, Unicode, UnicodeText
from sqlalchemy import event
from sqlalchemy.dialects.mysql import LONGTEXT
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, backref
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy_i18n import make_translatable, translation_base, Translatable

make_translatable(options={'locales': ['pt', 'en'],
                           'auto_create_locales': True,
                           'fallback_locale': 'en'})

db = SQLAlchemy()


# noinspection PyClassHasNoInit
class DeploymentTargetType:
    DOCKER = 'DOCKER'
    KUBERNETES = 'KUBERNETES'
    MARATHON = 'MARATHON'
    SUPERVISOR = 'SUPERVISOR'

    @staticmethod
    def values():
        return [n for n in list(DeploymentTargetType.__dict__.keys())
                if n[0] != '_' and n != 'values']


# noinspection PyClassHasNoInit
class DeploymentStatus:
    ERROR = 'ERROR'
    EDITING = 'EDITING'
    SAVED = 'SAVED'
    RUNNING = 'RUNNING'
    STOPPED = 'STOPPED'
    SUSPENDED = 'SUSPENDED'
    PENDING = 'PENDING'
    DEPLOYED = 'DEPLOYED'
    PENDING_UNDEPLOY = 'PENDING_UNDEPLOY'
    DEPLOYED_OLD = 'DEPLOYED_OLD'

    @staticmethod
    def values():
        return [n for n in list(DeploymentStatus.__dict__.keys())
                if n[0] != '_' and n != 'values']


# noinspection PyClassHasNoInit
class DeploymentType:
    MODEL = 'MODEL'
    DASHBOARD = 'DASHBOARD'
    APP = 'APP'

    @staticmethod
    def values():
        return [n for n in list(DeploymentType.__dict__.keys())
                if n[0] != '_' and n != 'values']

# Association tables definition


class Client(db.Model):
    """ Service client configuration """
    __tablename__ = 'client'

    # Fields
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    enabled = Column(Boolean, nullable=False)
    token = Column(String(256), nullable=False)

    # Associations
    deployment_id = Column(Integer,
                           ForeignKey("deployment.id",
                                      name="fk_client_deployment_id"),
                           nullable=False,
                           index=True)
    deployment = relationship(
        "Deployment",
        overlaps='clients',
        foreign_keys=[deployment_id])

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<Instance {}: {}>'.format(self.__class__, self.id)


class Deployment(db.Model):
    """ Deployment """
    __tablename__ = 'deployment'

    # Fields
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    version = Column(Integer, nullable=False)
    internal_name = Column(String(100))
    description = Column(String(400))
    created = Column(DateTime,
                     default=func.now(), nullable=False)
    updated = Column(DateTime,
                     default=func.now(), nullable=False,
                     onupdate=datetime.datetime.utcnow)
    command = Column(String(5000))
    workflow_name = Column(String(200),
                           default='')
    workflow_id = Column(Integer)
    job_id = Column(Integer)
    model_id = Column(Integer)
    model_name = Column(String(200), nullable=False)
    user_id = Column(Integer, nullable=False)
    user_login = Column(String(100), nullable=False)
    user_name = Column(String(100), nullable=False)
    enabled = Column(Boolean,
                     default=False, nullable=False)
    current_status = Column(Enum(*list(DeploymentStatus.values()),
                                 name='DeploymentStatusEnumType'),
                            default=DeploymentStatus.PENDING, nullable=False)
    type = Column(Enum(*list(DeploymentType.values()),
                       name='DeploymentTypeEnumType'),
                  default=DeploymentType.MODEL, nullable=False)
    attempts = Column(Integer,
                      default=0, nullable=False)
    log = Column(LONGTEXT)
    entry_point = Column(String(800))
    replicas = Column(Integer,
                      default=1, nullable=False)
    request_memory = Column(String(200),
                            default='128M', nullable=False)
    limit_memory = Column(String(200))
    request_cpu = Column(String(20),
                         default='500m')
    limit_cpu = Column(String(20),
                       default='1000m')
    base_service_url = Column(String(500))
    port = Column(Integer)
    extra_parameters = Column(LONGTEXT)
    input_spec = Column(LONGTEXT)
    output_spec = Column(LONGTEXT)
    assets = Column(LONGTEXT)
    execution_id = Column(String(200))

    # Associations
    target_id = Column(Integer,
                       ForeignKey("deployment_target.id",
                                  name="fk_deployment_target_id"),
                       nullable=False,
                       index=True)
    target = relationship(
        "DeploymentTarget",
        overlaps='deployments',
        foreign_keys=[target_id])
    image_id = Column(Integer,
                      ForeignKey("deployment_image.id",
                                 name="fk_deployment_image_id"),
                      nullable=False,
                      index=True)
    image = relationship(
        "DeploymentImage",
        overlaps='deployments',
        foreign_keys=[image_id])

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<Instance {}: {}>'.format(self.__class__, self.id)


class DeploymentImage(db.Model):
    """ Deployment image """
    __tablename__ = 'deployment_image'

    # Fields
    id = Column(Integer, primary_key=True)
    description = Column(String(200), nullable=False)
    name = Column(String(100), nullable=False)
    tag = Column(String(100), nullable=False)
    enabled = Column(Boolean, nullable=False)

    def __str__(self):
        return self.description

    def __repr__(self):
        return '<Instance {}: {}>'.format(self.__class__, self.id)


class DeploymentLog(db.Model):
    """ Logs for deployment """
    __tablename__ = 'deployment_log'

    # Fields
    id = Column(Integer, primary_key=True)
    date = Column(DateTime,
                  default=datetime.datetime.utcnow, nullable=False)
    status = Column(Enum(*list(DeploymentStatus.values()),
                         name='DeploymentStatusEnumType'), nullable=False)
    log = Column(LONGTEXT, nullable=False)

    # Associations
    deployment_id = Column(Integer,
                           ForeignKey("deployment.id",
                                      name="fk_deployment_log_deployment_id"),
                           nullable=False,
                           index=True)
    deployment = relationship(
        "Deployment",
        overlaps='logs',
        foreign_keys=[deployment_id])

    def __str__(self):
        return self.date

    def __repr__(self):
        return '<Instance {}: {}>'.format(self.__class__, self.id)


class DeploymentMetric(db.Model):
    """ Metrics for deployment """
    __tablename__ = 'deployment_metric'

    # Fields
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    parameters = Column(String(1000), nullable=False)
    enabled = Column(Boolean, nullable=False)
    user_id = Column(Integer, nullable=False)
    user_login = Column(String(100), nullable=False)

    # Associations
    deployment_id = Column(Integer,
                           ForeignKey("deployment.id",
                                      name="fk_deployment_metric_deployment_id"),
                           nullable=False,
                           index=True)
    deployment = relationship(
        "Deployment",
        overlaps='metrics',
        foreign_keys=[deployment_id])

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<Instance {}: {}>'.format(self.__class__, self.id)


class DeploymentTarget(db.Model):
    """ Deployment target """
    __tablename__ = 'deployment_target'

    # Fields
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    namespace = Column(String(100), nullable=False)
    volume_path = Column(String(250), nullable=False)
    description = Column(String(400))
    url = Column(String(500), nullable=False)
    authentication_info = Column(String(2500))
    enabled = Column(Boolean, nullable=False)
    base_service_url = Column(String(500), nullable=False)
    port = Column(Integer, nullable=False)
    target_type = Column(Enum(*list(DeploymentTargetType.values()),
                              name='DeploymentTargetTypeEnumType'), nullable=False)
    descriptor = Column(LONGTEXT)

    def __str__(self):
        return self.name

    def __repr__(self):
        return '<Instance {}: {}>'.format(self.__class__, self.id)


class MetricValue(db.Model):
    """ Metric values """
    __tablename__ = 'metric_value'

    # Fields
    id = Column(Integer, primary_key=True)
    sent_time = Column(DateTime)
    time = Column(DateTime, nullable=False)
    probe_id = Column(Integer, nullable=False)
    resource_id = Column(Integer, nullable=False)
    data = Column(LONGTEXT, nullable=False)
    item = Column(String(200))
    sent = Column(String(200), nullable=False)

    # Associations
    deployment_id = Column(Integer,
                           ForeignKey("deployment.id",
                                      name="fk_metric_value_deployment_id"),
                           nullable=False,
                           index=True)
    deployment = relationship(
        "Deployment",
        overlaps='metrics',
        foreign_keys=[deployment_id])

    def __str__(self):
        return self.sent_time

    def __repr__(self):
        return '<Instance {}: {}>'.format(self.__class__, self.id)

