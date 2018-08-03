# -*- coding: utf-8 -*-
import datetime
import json
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Float, \
    Enum, DateTime, Numeric, Text, Unicode, UnicodeText
from sqlalchemy import event
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, backref
from sqlalchemy.schema import UniqueConstraint
from sqlalchemy_i18n import make_translatable, translation_base, Translatable
from sqlalchemy.dialects.mysql import LONGTEXT
make_translatable(options={'locales': ['pt', 'en', 'es'],
                           'auto_create_locales': True,
                           'fallback_locale': 'en'})

db = SQLAlchemy()


# noinspection PyClassHasNoInit
class DeploymentType:
    DOCKER = 'DOCKER'
    SUPERVISOR = 'SUPERVISOR'
    MARATHON = 'MARATHON'
    KUBERNETES = 'KUBERNETES'

    @staticmethod
    def values():
        return [n for n in DeploymentType.__dict__.keys()
                if n[0] != '_' and n != 'values']


# noinspection PyClassHasNoInit
class DeploymentStatus:
    RUNNING = 'RUNNING'
    STOPPED = 'STOPPED'
    SUSPENDED = 'SUSPENDED'

    @staticmethod
    def values():
        return [n for n in DeploymentStatus.__dict__.keys()
                if n[0] != '_' and n != 'values']


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
                           ForeignKey("deployment.id"), nullable=False)
    deployment = relationship(
        "Deployment",
        foreign_keys=[deployment_id])

    def __unicode__(self):
        return self.name

    def __repr__(self):
        return '<Instance {}: {}>: {}'.format(self.__class__, self.id,
                                              unicode(self))


class Deployment(db.Model):
    """ Deployment """
    __tablename__ = 'deployment'

    # Fields
    id = Column(Integer, primary_key=True)
    description = Column(String(400), nullable=False)
    workflow_id = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False)
    user_login = Column(String(100), nullable=False)
    user_name = Column(String(100), nullable=False)
    enabled = Column(Boolean, nullable=False)
    current_status = Column(Enum(*DeploymentStatus.values(),
                                 name='DeploymentStatusEnumType'), nullable=False)
    attempts = Column(Integer,
                      default=0, nullable=False)
    log = Column(LONGTEXT)
    entry_point = Column(String(800), nullable=False)

    # Associations
    target_id = Column(Integer,
                       ForeignKey("deployment_target.id"), nullable=False)
    target = relationship(
        "DeploymentTarget",
        foreign_keys=[target_id])
    image_id = Column(Integer,
                      ForeignKey("deployment_image.id"), nullable=False)
    image = relationship(
        "DeploymentImage",
        foreign_keys=[image_id])

    def __unicode__(self):
        return self.description

    def __repr__(self):
        return '<Instance {}: {}>: {}'.format(self.__class__, self.id,
                                              unicode(self))


class DeploymentImage(db.Model):
    """ Deployment image """
    __tablename__ = 'deployment_image'

    # Fields
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    tag = Column(String(100), nullable=False)
    enabled = Column(Boolean, nullable=False)

    def __unicode__(self):
        return self.name

    def __repr__(self):
        return '<Instance {}: {}>: {}'.format(self.__class__, self.id,
                                              unicode(self))


class DeploymentTarget(db.Model):
    """ Deployment target """
    __tablename__ = 'deployment_target'

    # Fields
    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(400))
    url = Column(String(500), nullable=False)
    authentication_info = Column(String(500))
    enabled = Column(Boolean, nullable=False)
    target_type = Column(Enum(*DeploymentType.values(),
                              name='DeploymentTypeEnumType'), nullable=False)

    def __unicode__(self):
        return self.name

    def __repr__(self):
        return '<Instance {}: {}>: {}'.format(self.__class__, self.id,
                                              unicode(self))

