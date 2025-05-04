import pulumi
from pulumi_kubernetes.core.v1 import Service
from pulumi_kubernetes.networking.v1 import (
    Ingress, IngressSpecArgs, IngressRuleArgs, IngressTLSArgs,
    HTTPIngressRuleValueArgs, HTTPIngressPathArgs,
    IngressBackendArgs, IngressServiceBackendArgs, ServiceBackendPortArgs
)
from pulumi_kubernetes.helm.v3 import Release, ReleaseArgs, RepositoryOptsArgs
from .utils import create_tls_secret

def create_controller(namespace: str):
   nginx = Release(
        "ingress-nginx-controller",
        ReleaseArgs(
            chart="ingress-nginx",
            name="ingress-nginx",
            namespace=namespace,
            dependency_update = True,
            create_namespace=True,
            cleanup_on_fail=True,
            timeout=500,
            atomic=True,
            repository_opts=RepositoryOptsArgs(
                repo="https://kubernetes.github.io/ingress-nginx",
            ),
            values={
                "controller": {
                    "service": {
                      "loadBalancerIP": '10.0.1.10',
                      'externalTrafficPolicy': "Local"
                    },                    
                    "resources":{
                        "requests": {
                            "cpu": '20m',
                            "memory": '5Mi'
                        }
                    },
                    "admissionWebhooks" :{
                        "enabled": False
                    },
                    "publishService": {
                        "enabled": True
                    },
                    "allowSnippetAnnotations": True,
                    "config":{
                        "use-forwarded-headers": True,
                        'proxy-send-timeout': '600',
                        'proxy-read-timeout': '600',
                        'proxy-connect-timeout': '600',
                        'client-body-timeout': '600',
                        'client-header-timeout': '600',
                        'upstream-keepalive-timeout': '600',
                        'keep-alive': '600',
                        'proxy-body-size': "300m"
                    }
                }
            }
        ),
        name="ingress-nginx-controller"
    )
   return nginx


def default_annotations():
    return {
        'nginx.ingress.kubernetes.io/proxy-connect-timeout': '600',
        'nginx.ingress.kubernetes.io/proxy-read-timeout': '600',
        'nginx.ingress.kubernetes.io/proxy-send-timeout': '600',
        'nginx.ingress.kubernetes.io/ssl-redirect': 'false',
        'nginx.ingress.kubernetes.io/enable-cors': "true",
        'nginx.ingress.kubernetes.io/cors-allow-origin': '*',
    }
    
def register_ingress(name, namespace: str, host: str, services: list[Service], paths: list[str], extra__annots: dict = None, path_type: str = None, tls=True):
    annot = default_annotations();
    
    if extra__annots:
        annot.update(extra__annots)
    #if tls:
    #    _ = create_tls_secret(f'{name}-secret', namespace=namespace, cert=f'./certs/{host}.crt', key=f'./certs/{host}.key')
        
    Ingress(f'{name}-nginx-ingress',
                    metadata={
                        'namespace': namespace,
                        'annotations': annot
                    },
                    spec=IngressSpecArgs(
                        tls=[
                            IngressTLSArgs(hosts=[host], secret_name=f'{name}-secret')
                        ] if tls else None,
                        ingress_class_name='nginx',
                        rules=[IngressRuleArgs(
                            host=host,
                            http=HTTPIngressRuleValueArgs(
                                paths=list(map(lambda val: HTTPIngressPathArgs(
                                    path=f'/{val[1]}',
                                    path_type=path_type or 'Prefix',
                                    backend=IngressBackendArgs(
                                        service=IngressServiceBackendArgs(
                                            name=val[0].metadata.name,
                                            port=ServiceBackendPortArgs(
                                                number=val[0].spec.ports[0].port
                                            )
                                        )
                                    )
                                ), zip(services, paths))))
                        )]
                    )
            )


