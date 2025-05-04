from pulumi import ResourceOptions
from pulumi_kubernetes.core.v1 import (
    PersistentVolumeClaim,
    PersistentVolumeClaimSpecArgs,
    ResourceRequirementsArgs,
    EnvVarArgs,
    VolumeArgs,
    VolumeMountArgs,
    PersistentVolumeClaimVolumeSourceArgs
)
from pulumi_kubernetes.meta.v1 import ObjectMetaArgs
from components.serviceDeployment import ServiceDeployment
from components.ingress import register_ingress

class VaultWarden(ServiceDeployment):
    """Wrapper class for deploying a VaultWarden Service"""
    
    name: str
    """Unique name for the deployment."""
    
    domain: str
    """Domain the vault it being hosted."""
    
    _image: str = "vaultwarden/server"
    """Container image used to run the server."""
    
    def __init__(self, name: str, namespace: str, domain: str, opts: ResourceOptions = None):
        self.domain = domain;
        self.name = name
        super().__init__(name, self._image, 
                        namespace,
                        opts,
                        ports=[80],
                        env_vars=[EnvVarArgs(name='DOMAIN', value=f'http://{domain}')])
        self.__create_pvc(namespace, storage_request='2Gi')
        register_ingress(
            name,
            namespace, 
            self.domain, 
            [self.service], 
            [''], {
                'nginx.ingress.kubernetes.io/use-regex': '"true"',
                'nginx.ingress.kubernetes.io/rewrite-target': '/'
            })
        # TODO: init backups
        
        
    def __create_pvc(self, namespace: str, storage_request: str):
        """Creates a PVC for the vault deployment.

        Args:
            namespace (str): Deployment namespace
            storage_request (str): Amount of storage requested.
        """
        PersistentVolumeClaim(self.name,
        metadata=ObjectMetaArgs(
            name=f'{self.name}-data',
            namespace=namespace
        ),
        spec=PersistentVolumeClaimSpecArgs(
            access_modes=["ReadWriteOnce"],
            resources=ResourceRequirementsArgs(
                requests={
                    "storage": storage_request,
                },
            ),
        ))
        
    def _volume_mounts(self):
        return [VolumeMountArgs(
                mount_path="/data",
                name=f'{self.name}-data',
                sub_path="vault",
            )]
        
    def _volumes(self):
        return [VolumeArgs(name=f'{self.name}-data',
                    persistent_volume_claim=PersistentVolumeClaimVolumeSourceArgs(
                        claim_name=f'{self.name}-data',
                    ),
                )]