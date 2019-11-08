# -*- coding: utf-8 -*-}
import logging
import os

from flask import request
from flask_restful import Resource
from tmalibrary.actuator import *

log = logging.getLogger(__name__)


def _patch_tma():
    """ Monkey patches TMA methods in order to them work with Python 3.5"""

    # noinspection PyPep8Naming
    def getPrivateKey(self, filename):
        try:
            # Needs to be read as binary
            private_key = open(filename, 'rb').read()
            return private_key

        except EnvironmentError as e:
            print(os.strerror(e.errno))
            return None

    # noinspection PyPep8Naming
    def getPublicKey(self, filename):
        try:
            # Needs to be read as binary
            return open(filename, 'rb').read()
        except EnvironmentError as e:
            print(os.strerror(e.errno))
            return None

    original_sign = KeyManager.sign

    def sign(self, data, keyFile):
        return original_sign(self, data.encode('utf8'), keyFile)

    # KeyManager.sign = sign
    KeyManager.getPrivateKey = getPrivateKey
    KeyManager.getPublicKey = getPublicKey


class TMAActuatorApi(Resource):
    DENY_DEPLOY = 'DENY_DEPLOY'
    SEND_EMAIL = 'SEND_EMAIL'
    DISABLE_SERVICE = 'DISABLE_SERVICE'
    RETRAIN = 'RETRAIN'

    def __init__(self):
        _patch_tma()

    def post(self):
        from seed.jobs import tma_deny_deploy, tma_disable_service, \
            tma_retrain, tma_send_email
        message = HandleRequest()

        data_input = request.data
        if data_input is None or data_input == b'':
            return message.generateResponse('Empty request'.encode('utf8'))

        payload = message.processRequest(data_input)

        try:
            # Resource Id can be obtained? What about other fields?
            operation = 'Successfully executed action {}'.format(payload.action)
            if payload.action == self.DENY_DEPLOY:
                tma_deny_deploy.queue(payload)
            elif payload.action == self.SEND_EMAIL:
                tma_send_email.queue(payload)
            elif payload.action == self.DISABLE_SERVICE:
                tma_disable_service.queue(payload)
            elif payload.action == self.RETRAIN:
                tma_retrain.queue(payload)
            else:
                operation = 'Invalid action: {}'.format(payload.action)
        except Exception as ex:
            operation = "An exception has occurred: {}".format(ex)
        return message.generateResponse(str(operation))
