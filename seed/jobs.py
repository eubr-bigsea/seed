# coding=utf-8
import datetime
import json
import logging.config
import os
import yaml
from tmalibrary.probes import *
from flask_babel import gettext as babel_gettext, force_locale
from seed import rq
from seed.app import app
from seed.models import Deployment, DeploymentLog, DeploymentStatus, \
    Traceability, db, AuditableType
import requests
logging.config.fileConfig('logging_config.ini')
logger = logging.getLogger(__name__)

JOB_MODULE = True
def send_message(self, message_formated):
    # url = 'http://0.0.0.0:5000/monitor'
    self.message_formated = message_formated
    headers = {'content-type': 'application/json'}
    # return the response from Post request
    return requests.post(self.url, data=self.message_formated, headers=headers, verify=False)

def get_config():
    config_file = os.environ.get('SEED_CONFIG')
    if config_file is None:
        raise ValueError(
            'You must inform the SEED_CONF env variable')

    with open(config_file) as f:
        config = yaml.load(f, Loader=yaml.FullLoader)
    return config['seed']

def ctx_gettext(locale):
    def translate(msg, **variables):
        with app.app.test_request_context():
            with force_locale(locale):
                return babel_gettext(msg, **variables)

    return translate

@rq.job("seed", result_ttl=3600)
def metric_probe_updater(data):
    """ A generic client for TMA """
    config = get_config()

    msg = Message(probeId=data.get('probe_id'),
    resourceId=data.get('resource'),
        messageId=data.get('message_id'),
        sentTime=data.get('sent_time'),
        data=None)
    dt = Data(type="measurement",
              descriptionId=data.get('description_id'),
              observations=[Observation(time=data.get('observation_time'),
                                        value=data.get('observation_value'))])
    msg.add_data(data=dt)
    json_msg = json.dumps(msg.reprJSON(), cls=ComplexEncoder)
    logging.debug('%s' % json_msg)

    Communication.send_message= send_message
    communication = Communication(config['services']['tma']['url'])

    communication.send_message(json_msg)

@rq.job("seed", result_ttl=3600)
def auditing(data):
    logs = json.loads(data)

    for log in logs:
        workflow = log.pop('workflow')
        log['source_id'] = workflow['id']
        log['source_type'] = AuditableType.WORKFLOW
        data_sources = log.pop('data_sources')
        log['created'] = datetime.datetime.strptime(log.pop('date')[:18],
                                                    "%Y-%m-%dT%H:%M:%S")
        user = log.pop('user')
        log['user_id'] = user.get('id')
        log['user_login'] = user.get('login')
        log['user_name'] = user.get('name')
        log['action'] = log.pop('event')
        if 'job' in log:
            log['job_id'] = log.get('job', {}).get('id')
            del log['job']

        log['workflow_id'] = workflow['id']
        log['workflow_name'] = workflow['name']

        task = log.pop('task')
        log['task_id'] = task['id']
        log['task_name'] = task['name']
        log['task_type'] = task['type']
        log['risk_score'] = 0.0

        for ds in data_sources:
            log['target_id'] = ds
            log['target_type'] = AuditableType.DATA_SOURCE
            trace = Traceability(**log)
            db.session.add(trace)
    db.session.commit()


@rq.job("seed", ttl=60, result_ttl=3600)
def deploy3():
    import pdb
    pdb.set_trace()
    print((Deployment.query.all()))


@rq.exception_handler
def report_jobs_errors(job, *exc_info):
    print(('ERROR', job, exc_info))


@rq.job
def deploy2(deployment_id):
    deployment = Deployment.query.get(deployment_id)
    print(('#' * 20, deployment.id, deployment.created))
    log_message_for_deployment(deployment_id, "Teste", DeploymentStatus.ERROR)


@rq.job
def deploy(deployment_id, locale):
    # noinspection PyBroadException

    gettext = ctx_gettext(locale)
    try:
        deployment = Deployment.query.get(deployment_id)
        if deployment:
            if logger.isEnabledFor(logging.INFO) or True:
                logger.info('Running job for deployment %s', deployment_id)

            log_message = gettext('Successfully deployed as a service')
            log_message_for_deployment(deployment_id, log_message,
                                       status=DeploymentStatus.DEPLOYED)
        else:
            log_message = gettext(
                locale, 'Deployment information with id={} not found'.format(
                    deployment_id))

            log_message_for_deployment(deployment_id, log_message,
                                       status=DeploymentStatus.ERROR)

    except Exception as e:
        logger.exception('Running job for deployment %s')
        log_message = gettext(
            'Error in deployment {}: \n {}'.format(deployment_id, str(e)))
        log_message_for_deployment(deployment_id, log_message,
                                   status=DeploymentStatus.ERROR)


def log_message_for_deployment(deployment_id, log_message, status):
    log = DeploymentLog(
        status=status, deployment_id=deployment_id, log=log_message)
    DeploymentLog.query.session.add(log)
    DeploymentLog.query.session.commit()
