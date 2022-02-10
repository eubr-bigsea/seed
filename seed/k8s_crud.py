import requests
from flask import current_app
from kubernetes import client, config
from urllib import parser
########### Deployment ###########
START_PORT = 31160


def _handle_cpu_limit(limit):
    if not limit.endswith('m'):
        return limit + 'm'
    return limit


def _get_model_url(model_id: int) -> str:
    config = current_app.config['SEED_CONFIG']
    limonero_config = config['services']['limonero']
    resp = requests.get(f"{limonero_config['url']}/models/{model_id}",
                        headers={'X-Auth-Token': str(limonero_config['auth_token'])})
    data = resp.json()
    return data['storage']['url'] + data['path']


def create_deployment(deployment, deployment_image, deployment_target, api):

    #Table: Pod
    pod_name = deployment.internal_name
    pod_replicas = deployment.replicas
    container_port = "80"

    model_url = _get_model_url(deployment.model_id)
    #Table: Deployment

    deployment_version = "apps/v1"
    deployment_kind = "Deployment"

    parsed = parser.urlparse(model_url)
    using_file = False
    if parsed.scheme == 'file':
        using_file = True
        model_url = parsed.path

    container = client.V1Container(
        name=pod_name,
        image=f'{deployment_image.name}:{deployment_image.tag}',
        image_pull_policy="Always",
        ports=[client.V1ContainerPort(container_port=int(container_port))],
        resources=client.V1ResourceRequirements(
            requests={"cpu": _handle_cpu_limit(deployment.request_cpu),
                      "memory": deployment.request_memory},
            limits={"cpu": _handle_cpu_limit(deployment.limit_cpu),
                    "memory": deployment.limit_memory},
        ),
        env=[
            client.V1EnvVar(name="MLEAP_MODEL", value=model_url),
        ]
    )
    if using_file:
        # Maps HDFS storage
	pvc = client.V1PersistentVolumeClaim(
	        api_version='v1',
        	kind='PersistentVolumeClaim',
	        metadata=client.V1ObjectMeta(
        	    name='hdfs-pvc'
	        )
	)


    # Create and configure a spec section.
    template = client.V1PodTemplateSpec(
        metadata=client.V1ObjectMeta(labels={
            'app': pod_name,
            'seed/deployment-version': str(deployment.version)
        }),
        spec=client.V1PodSpec(containers=[container]),
    )

    spec = client.V1DeploymentSpec(
        replicas=int(pod_replicas), template=template, selector={
            "matchLabels":
            {"app": pod_name}})
    # Instantiate the deployment object
    deployment_obj = client.V1Deployment(
        api_version=deployment_version,
        kind=deployment_kind,
        metadata=client.V1ObjectMeta(
            name=deployment.internal_name,
            labels={
                'seed/deployment-version': str(deployment.version)
            }), spec=spec,
    )
    # import pdb; pdb.set_trace()

    ns = deployment_target.namespace
    if _deployment_exists(api, ns, deployment.internal_name):
        api.patch_namespaced_deployment(name=deployment.internal_name,
                                        body=deployment_obj, namespace=ns)
    else:
        api.create_namespaced_deployment(body=deployment_obj, namespace=ns)

    # Create service
    target_port = deployment_target.port

    deployment.port = create_service(deployment.internal_name,
                                     deployment_target.namespace, target_port, 
                                     deployment.port, api)


def _get_next_port(services):
    ports = [START_PORT]
    for service in (services or []):
        service_ports = service.get('spec', {}).get('ports',[]) or []
        ports += [p.get('port', 0) for p in service_ports]

    return max(ports) + 1


def delete_deployment(deployment, deploymentTarget, api):

    ret = api.delete_namespaced_deployment(
        name=deployment.internal_name,
        namespace=deploymentTarget.namespace,
        body=client.V1DeleteOptions(
            propagation_policy="Foreground", grace_period_seconds=5
        ),
    )

    # Delete service
    try:
        api_core = client.CoreV1Api()
        service_name = _get_service_name(deployment.name)
        delete_service(service_name, deploymentTarget.namespace, api_core)
    except:
        pass


def _deployment_exists(api, namespace: str, deployment_name: str) -> bool:
    resp = api.list_namespaced_deployment(namespace=namespace)
    for i in resp.items:
        if i.metadata.name == deployment_name:
            return True
    return False

########### Service ##########


def _get_all_services(api: client.CoreV1Api):
    field_selector = 'metadata.namespace!=kube-system,metadata.namespace!=default'
    services = api.list_service_for_all_namespaces(
        field_selector=field_selector, watch=False)
    return services.to_dict().get('items')


def create_service(deployment_name: str, namespace: str,
                   target_port: int, port: int, api) -> int:

    #import pdb
    # pdb.set_trace()

    api_core = client.CoreV1Api(api_client=api.api_client)
    services = _get_all_services(api_core)

    service_name = _get_service_name(deployment_name)
    service_exists = False
    for s in services:
        if s.get('metadata', {}).get('name') == service_name:
            service_exists = True
            #port = s['spec']['ports'][0]['node_port']
            break

    if port is None:
        port = _get_next_port(services)

    # User interface parameters
    version = "v1"
    kind = "Service"

    body = client.V1Service(
        api_version=version,
        kind=kind,
        metadata=client.V1ObjectMeta(
            name=service_name
        ),
        spec=client.V1ServiceSpec(
            selector={"app": deployment_name},
            ports=[client.V1ServicePort(
                name='api',
                node_port=int(port),
                port=int(target_port),
                target_port=int(target_port),
                protocol='TCP',
            )],
            type='NodePort'
        )
    )

    try:
        if service_exists:
        #api_core.patch_namespaced_service(name=service_name,
        #                                  namespace=deployment_namespace, body=body)
            delete_service(service_name, namespace, api_core)
            #api_core.delete_namespaced_service(name=service_name, 
            #    namespace=namespace)
    except:
        pass
    api_core.create_namespaced_service(namespace=namespace,
                                       body=body)

    return port


def _get_service_name(deployment_name):
    service_name = 's' + deployment_name[1:]
    return service_name


def delete_service(service_name, deployment_namespace, api):

    ret = api.delete_namespaced_service(
        name=service_name,
        namespace=deployment_namespace,
    )
