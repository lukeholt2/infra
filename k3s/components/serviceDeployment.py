from typing import Sequence

import pulumi
from pulumi import ResourceOptions, ComponentResource, Output
from pulumi_kubernetes.apps.v1 import Deployment, DeploymentSpecArgs
from pulumi_kubernetes.core.v1 import (
    ContainerArgs,
    ContainerPortArgs,
    PodSpecArgs,
    PodTemplateSpecArgs,
    ResourceRequirementsArgs,
    Service,
    ServicePortArgs,
    ServiceSpecArgs,
    EnvVarArgs
)
from pulumi_kubernetes.meta.v1 import LabelSelectorArgs, ObjectMetaArgs


class ServiceDeployment(ComponentResource):
    deployment: Deployment
    service: Service
    ip_address: Output[str]

    def __init__(self, name: str, image: str,
                 namespace: str,
                 resources: ResourceRequirementsArgs = None, replicas: int = None,
                 ports: Sequence[int] = None, 
                 allocate_ip_address: bool = None,
                 env_vars: list[EnvVarArgs] = None,
                 node_name: str = None,
                 opts: ResourceOptions = None):
        super().__init__('k8sx:component:ServiceDeployment', name, {}, opts)

        labels = {"app": name}
        container = ContainerArgs(
            name=name,
            image=image,
            env=env_vars,
            volume_mounts=self._volume_mounts(),
            resources=resources or ResourceRequirementsArgs(
                requests={
                    "cpu": "10m",
                    "memory": "10Mi"
                },
            ),
            ports=[ContainerPortArgs(container_port=p) for p in ports] if ports else None,
        )
        self.deployment = Deployment(
            name,
            metadata=ObjectMetaArgs(
                namespace=namespace
            ),
            spec=DeploymentSpecArgs(
                selector=LabelSelectorArgs(match_labels=labels),
                replicas=replicas if replicas is not None else 1,
                template=PodTemplateSpecArgs(
                    metadata=ObjectMetaArgs(labels=labels),
                    spec=PodSpecArgs(containers=[container], node_name=node_name, volumes=self._volumes()),
                ),
            ),
            opts=pulumi.ResourceOptions(parent=self))
        self.service = Service(
            name,
            metadata=ObjectMetaArgs(
                name=name,
                namespace=namespace,
                labels=self.deployment.metadata.apply(lambda m: m.labels),
            ),
            spec=ServiceSpecArgs(
                ports=[ServicePortArgs(port=p, target_port=p) for p in ports] if ports else None,
                selector=self.deployment.spec.apply(lambda s: s.template.metadata.labels),
                type=("LoadBalancer") if allocate_ip_address else None,
            ),
            opts=pulumi.ResourceOptions(parent=self))
        if allocate_ip_address:
            ingress=self.service.status.apply(lambda s: s.load_balancer.ingress[0])
            self.ip_address = ingress.apply(lambda i: i.ip or i.hostname or "")
        self.register_outputs({})
        
        
    def _volume_mounts(self):
        return None
    
    def _volumes(self):
        return None