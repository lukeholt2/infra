import pulumi
from pulumi import ResourceOptions
from pulumi_kubernetes.core.v1 import EnvVarArgs
from components.serviceDeployment import ServiceDeployment
from components.postgres import Postgres, PostgresSettings
from components.ingress import register_ingress


class ExpenseApp:
    """Internal deployment of the plutus expense app"""
    
    domain: str
    """Domain URL of the deployed app."""

    api: ServiceDeployment
    """Service deployment instance of the API"""
    
    ui: ServiceDeployment
    """Service deployment instance of the UI"""
    
    db: Postgres
    """Backend Postgres deployment"""
    
    def __init__(self, target_namespace: str, domain: str, ui_version: str, api_version: str):
        config = PostgresSettings.from_config();
        self.db = Postgres('expenseapp-db', target_namespace, config)
        self.domain = domain
    
        self.api = ServiceDeployment(
            "expenseapi",
            image=f'gitlab.internal.oasis.com:5005/gitlab-instance-8c9d9f19/expenseapp:{api_version}',
            namespace=target_namespace,
            ports=[8080],
            opts=ResourceOptions(depends_on=self.db),
            env_vars=[
                EnvVarArgs(name="ConnectionStrings__PostgresConnection", value=self.db.connection_string()),
                EnvVarArgs(name="ASPNETCORE_ENVIRONMENT", value="Production")
            ]
        )
        
        self.ui = ServiceDeployment(
            "plutus",
            image=f'gitlab.internal.oasis.com:5005/gitlab-instance-8c9d9f19/plutus:{ui_version}',
            namespace=target_namespace,
            ports=[3000],
            env_vars=[
                EnvVarArgs(name="NEXTAUTH_URL", value="expenseapp.com"),
                EnvVarArgs(name="API_URL", value=self.api.service.spec.apply(lambda s: f'http://{s.cluster_ip}:{s.ports[0].port}/api'))
            ],
            opts=ResourceOptions(depends_on=self.api)
        )
        
        register_ingress(
            "plutus",
            target_namespace, 
            self.domain, 
            [self.ui.service], 
            [''])
        
        register_ingress(
            "expenseapi",
            target_namespace, 
            self.domain,
            [self.api.service], 
            ['expenseapi(/|$)(.*)'],
            {
                'nginx.ingress.kubernetes.io/use-regex': '"true"',
                'nginx.ingress.kubernetes.io/rewrite-target': '/$2'
            }, tls=False
        )
