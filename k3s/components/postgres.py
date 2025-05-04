import pulumi
from pulumi import ResourceOptions, ComponentResource
from pulumi_kubernetes.core.v1 import (
    PersistentVolumeClaim,
    PersistentVolumeClaimSpecArgs,
    ResourceRequirementsArgs,
    PodTemplateSpecArgs,
    PodTemplateSpecArgs,
    PodSpecArgs,
    Service,
    ContainerArgs,
    ContainerPortArgs,
    EnvVarArgs,
    VolumeArgs,
    VolumeMountArgs,
    PersistentVolumeClaimVolumeSourceArgs,
    ServiceSpecArgs,
    ServicePortArgs,
    ServiceSpecType
)
from pulumi_kubernetes.meta.v1 import ObjectMetaArgs, ObjectMetaPatchArgs, LabelSelectorArgs
from pulumi_kubernetes.apps.v1 import Deployment, DeploymentSpecArgs


class PostgresSettings:
    user: str
    password: str
    db: str
    
    def __init__(self, user: str = None, password: str = None, db: str = None):
        self.user = user
        self.password = password
        self.db = db
    
    def from_config():
        config = pulumi.Config();
        return PostgresSettings(**config.require_object('postgres'))
    
    def as_env_args(self):
        return [
            EnvVarArgs(name='POSTGRES_USER', value=self.user),
            EnvVarArgs(name='POSTGRES_PASSWORD', value=self.password),
            EnvVarArgs(name='POSTGRES_DB', value=self.db),
            EnvVarArgs(name="POSTGRES_LISTEN_ADDRESS", value="*")
        ]
        

class Postgres(ComponentResource):
    name: str
    deployment: Deployment
    service: Service
    __settings: PostgresSettings
    
    def __init__(self, name: str, namespace: str, connection: PostgresSettings, storage_request: str = '5Gi', opts: ResourceOptions = None, node_name: str = None):
        super().__init__('k8sx:component:Postgres', name, {}, opts)
        self.name = name
        self.__settings = connection
        self.__create_pvc(namespace, storage_request)
        self.__create_deployment(namespace, connection, node_name)
        self.__register_service(namespace)
        
    def connection_string(self):
        user = self.__settings.user
        password = self.__settings.password
        db = self.__settings.db
        return self.service.spec.apply(lambda s: f'User ID={user};Password={password};Server={s.cluster_ip};Port=5432;Database={db};')
        
    def __create_pvc(self, namespace: str, storage_request: str):
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
        
    def __create_deployment(self, namespace: str, connection: PostgresSettings, node_name=None):
        self.deployment =  Deployment(self.name,
            metadata=ObjectMetaArgs(
                name=self.name,
                namespace=namespace
            ),
            spec=DeploymentSpecArgs(
                replicas=1,
                selector=LabelSelectorArgs(
                    match_labels={
                        'app': self.name
                    }
                ),
                template=PodTemplateSpecArgs(
                    metadata=ObjectMetaArgs(
                        labels={
                            'app': self.name
                        },
                        namespace=namespace
                    ),
                    spec=PodSpecArgs(
                        node_name=node_name,
                        containers=[ContainerArgs(
                            env=connection.as_env_args(),
                            image="postgres",
                            name="postgres",
                            ports=[ContainerPortArgs(
                                container_port=5432,
                                name=self.name
                            )],
                            volume_mounts=[VolumeMountArgs(
                                mount_path="/var/lib/postgresql/data",
                                name=f'{self.name}-data',
                                sub_path="postgres",
                            )],
                        )],
                        volumes=[VolumeArgs(
                            name=f'{self.name}-data',
                            persistent_volume_claim=PersistentVolumeClaimVolumeSourceArgs(
                                claim_name=f'{self.name}-data',
                            ),
                        )],
                    ),
                ),
            ))
        
    def __register_service(self, namespace: str):
        self.service = Service(self.name,
            metadata=ObjectMetaArgs(
                name=self.name,
                namespace=namespace
            ),
            spec=ServiceSpecArgs(
                type=ServiceSpecType.CLUSTER_IP,
                selector={
                    'app': self.name
                },
                ports=[ServicePortArgs(
                    name=self.name,
                    port=5432,
                    target_port=5432,
                    protocol='TCP'
                )]
            ))
