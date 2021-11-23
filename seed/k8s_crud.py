from kubernetes import client, config
#import pdb 

########### Deployment ###########
def create_deployment(deployment, deploymentImage, deploymentTarget, api): 
  
   #Table: Pod 
   pod_name       = deployment.name 
   pod_replicas   = deployment.replicas
   container_port = "80"

   #Table: Deployment
   deployment_name      = deployment.name 
   deployment_image     = deploymentImage.name 
   deployment_version   = "apps/v1" 
   deployment_kind      = "Deployment"
   deployment_namespace = deploymentTarget.namespace

   container = client.V1Container(
        name=pod_name,
        image=deployment_image,
        ports=[client.V1ContainerPort(container_port=int(container_port))],
        resources=client.V1ResourceRequirements(
            requests={"cpu": deployment.request_cpu, "memory": deployment.request_memory},
            limits={"cpu": deployment.limit_cpu, "memory": deployment.limit_memory},
       ),
   ) 

   #Create and configure a spec section.
   template = client.V1PodTemplateSpec(
       metadata=client.V1ObjectMeta(labels={"app": pod_name}),
       spec=client.V1PodSpec(containers=[container]),
   )

   spec       = client.V1DeploymentSpec(
                replicas=int(pod_replicas), template=template, selector={
                "matchLabels":
                {"app": pod_name}})

   # Instantiate the deployment object
   deployment_obj = client.V1Deployment(
                    api_version=deployment_version,
                    kind=deployment_kind,
                    metadata=client.V1ObjectMeta(name=deployment_name),
                    spec=spec,
   )

   ret = api.create_namespaced_deployment(
        body=deployment_obj, namespace=deployment_namespace
   )
   
   #Create service 
   api_core=client.CoreV1Api()
   port = deployment.port #expose service
   target_port = deploymentTarget.target_port
   create_service(deployment_name, deployment_namespace, port, target_port, api_core)

def delete_deployment(deployment, deploymentTarget, api):

   ret = api.delete_namespaced_deployment(
        name=deployment.name,
        namespace=deploymentTarget.namespace,
        body=client.V1DeleteOptions(
            propagation_policy="Foreground", grace_period_seconds=5
        ),
   )
  
   #Delete service 
   api_core=client.CoreV1Api()
   service_name = deployment.name + "-service"
   delete_service(service_name, deploymentTarget.namespace, api_core)

########### Service ##########
def create_service(deployment_name, deployment_namespace, port, target_port, api): 
 
  #User interface parameters      
  service_name = deployment_name + "-service"
  version      = "v1"
  kind         = "Service"
  port         = port #expose service
  target_port  = target_port 
  
  body = client.V1Service(
      api_version=version,
      kind=kind,
      metadata=client.V1ObjectMeta(
          name=service_name
      ),
      spec=client.V1ServiceSpec(
          selector={"app": deployment_name},
          ports=[client.V1ServicePort(
              name="port", 
              port=int(port),
              target_port=int(target_port)
          )]
      )
  )

  api.create_namespaced_service(namespace=deployment_namespace, body=body) 

def delete_service(service_name, deployment_namespace, api):

   ret = api.delete_namespaced_service(
        name=service_name,
        namespace=deployment_namespace,
   )
