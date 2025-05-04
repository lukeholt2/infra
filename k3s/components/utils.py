from base64 import encode
from pulumi_kubernetes.core.v1 import Secret, SecretArgs
from pulumi_kubernetes.meta.v1 import ObjectMetaArgs


def create_tls_secret(name: str, namespace: str, cert: str, key: str):
    """Create a new tls secret using the given cert + key

    Args:
        name (str): Name of the secret to create
        namespace (str): Target namespace to store the secret
        cert (str): Cert file path
        key (str): Key file path

    Returns:
        Secret: newly constructed k8s secret instance
    """
    data = []
    with open(cert,'rb') as c:
        data['tls.crt'] = encode(c)
    with open(key,'rb') as k:
        data['tls.key'] = encode(k)
        
    return Secret(name,
                metadata=ObjectMetaArgs(namespace=namespace),
                args=SecretArgs(
                    type='kubernetes.io/tls',
                    data=data
                )
            )