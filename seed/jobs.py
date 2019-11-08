# coding=utf-8
import datetime
import json
import logging.config
import os

import requests
import yaml
from flask_babel import gettext as babel_gettext, force_locale
from seed import rq
from seed.app import app
from seed.models import Deployment, DeploymentLog, DeploymentStatus, \
    Traceability, db, AuditableType, MetricValue
from tmalibrary.probes import *

logging.config.fileConfig('logging_config.ini')
logger = logging.getLogger(__name__)

JOB_MODULE = True


def send_message(self, message_formated):
    """ Monkey patches TMA send message """
    self.message_formated = message_formated
    headers = {'content-type': 'application/json'}
    return requests.post(self.url, data=self.message_formated, headers=headers,
                         verify=False)


Communication.send_message = send_message


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
def metric_probe_updater(metric_data):
    # noinspection PyBroadException
    try:
        """ A generic client for TMA """
        config = get_config()
        tma_conf = config.get('services').get('tma', {})
        wf_mapping = tma_conf.get('workflows', {})
        description_mapping = tma_conf.get('descriptions', {})

        wf_id = metric_data.get('content', {}).get('workflow_id')
        if int(wf_id) not in wf_mapping:
            logger.warn('Workflow not mapped in TMA.')
            return

        description_id = metric_data.get('content', {}).get('metric')
        if description_id not in description_mapping:
            logger.warn('Description not mapped in TMA.')
            return

        logger.info(
            'Sending message with probeId=%s, resourceId=%s, '
            'descriptionId=%s, messageId=%s',
            tma_conf.get('probe_id'), wf_mapping.get(wf_id),
            description_mapping.get(description_id), wf_id)

        not_acceptable = next((x for x in metric_data['content']['values'] if
                               not x.get('acceptable', True)), None)
        now = datetime.datetime.now()
        if not_acceptable:

            mv = MetricValue(sent_time=None,
                             time=metric_data.get('time'),
                             probe_id=tma_conf.get('probe_id'),
                             resource_id=wf_mapping.get(int(wf_id)),
                             data=json.dumps(metric_data),
                             tma_data='',
                             item=not_acceptable.get('group'),
                             sent=not_acceptable.get('value'))

            msg = Message(probeId=tma_conf.get('probe_id'),
                          resourceId=wf_mapping.get(int(wf_id)),
                          messageId=None,  # incremental
                          sentTime=round(datetime.datetime.timestamp(now)),
                          data=None)
            observed = datetime.datetime.strptime(metric_data['time'][:19],
                                                  '%Y-%m-%dT%H:%M:%S')
            dt = Data(type="measurement",
                      descriptionId=description_mapping.get(description_id),
                      observations=[
                          Observation(
                              time=round(datetime.datetime.timestamp(observed)),
                              value=not_acceptable.get('value'))])
            msg.add_data(data=dt)

            db.session.add(mv)
            db.session.commit()

            msg.messageId = mv.id
            json_msg = json.dumps(msg.reprJSON(), cls=ComplexEncoder)
            logger.debug('%s', json_msg)

            # Communication.send_message = send_message
            tma_conn = Communication(config['services']['tma']['url'])
            response = tma_conn.send_message(json_msg)
            logger.info('TMA response (%s): %s', response.status_code,
                        response.text)
            if 'Number of errors' in response.text:
                raise ValueError('Error in TMA')
            mv.sent_time = now
            mv.tma_data = json_msg
            db.session.add(mv)
            db.session.commit()
        else:
            mv = MetricValue(sent_time=now,
                             time=metric_data.get('time'),
                             probe_id=tma_conf.get('probe_id'),
                             resource_id=wf_mapping.get(int(wf_id)),
                             data=json.dumps(metric_data),
                             tma_data=None,
                             item=None,
                             sent=now)
            db.session.add(mv)
            db.session.commit()
            logger.info('All metrics in acceptable range.')
    except Exception:
        logger.exception('Error in metric job')
        db.session.rollback()


@rq.job("seed", result_ttl=3600)
def auditing(auditing_data):
    logs = json.loads(auditing_data)

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


@rq.job
def tma_retrain(tma_payload):
    logger.info("TMA retrain")


@rq.job
def tma_disable_service(tma_payload):
    logger.info("TMA disable service")


@rq.job
def tma_send_email(tma_payload):
    logger.info("TMA Send Email")


@rq.job
def tma_deny_deploy(tma_payload):
    logger.info("TMA Deny deploy")
