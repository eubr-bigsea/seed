from .conftest import *
from flask import current_app


def test_unauthorized(client):
    rv = client.post('/deployments', headers=None)
    assert rv.json['status'] == 'ERROR'
    assert rv.status_code == 401

    rv = client.patch('/deployments/1', headers=None)
    assert rv.json['status'] == 'ERROR'
    assert rv.status_code == 401


def test_get_deployment_return_none(client):
    headers = {'X-Auth-Token': str(client.secret)}

    rv = client.get('/deployments/200', headers=headers)
    assert rv.status_code == 404
    assert rv.json['status'] == 'ERROR', rv.json['status']


def test_get_deployment(client):
    headers = {'X-Auth-Token': str(client.secret)}
    deployment_id = 101
    rv = client.get(
        f'/deployments/{deployment_id}?fields=title,data',
        headers=headers)

    v3 = rv.json['data'][0]
    assert rv.status_code == 200
    assert v3['name'] == 'everybody'

def test_post_deployment_invalid_form(client):
    headers = {'X-Auth-Token': str(client.secret)}
    data = {}
    rv = client.post('/deployments', headers=headers, json=data)
    
    assert rv.status_code == 400

