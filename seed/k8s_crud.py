from kubernetes import client, config
#import pdb 

def create_deployment(deployment, deploymentImage, api): 
  
   #Table: Pod 
   pod_name       = "nginx" 
   pod_replicas   = deployment.replicas
   container_port = "80"

   #Table: Deployment
   deployment_name      = "nginx-deployment" 
   deployment_image     = deploymentImage.name 
   deployment_version   = "apps/v1" 
   deployment_kind      = "Deployment"
   deployment_namespace = "default"

   container = client.V1Container(
        name=pod_name,
        image=deployment_image,
        ports=[client.V1ContainerPort(container_port=int(container_port))],
        #Update with deployment table attributes
        resources=client.V1ResourceRequirements(
            requests={"cpu": "100m", "memory": deployment.request_memory},
            limits={"cpu": "500m", "memory": deployment.limit_memory},
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
