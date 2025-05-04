import pulumi
from pulumi import Output, ComponentResource, ResourceOptions
from pulumi_kubernetes.core.v1 import Service
from pulumi_kubernetes.helm.v3 import Release, ReleaseArgs, RepositoryOptsArgs

class HelmRelease(ComponentResource):
    """Class defining a utility wrapper for deploying helm charts"""
    
    service: Service
    """The service deployed via the provided helm chart"""
    
    def __init__(self, name: str, namespace: str, repo: str, chart: str=None, values=None, yaml_values=None, hasService: bool =  True, opts: ResourceOptions = None):
        """Initialize a new helm release in the given namespace

        Args:
            name (str): Name of the created resource
            namespace (str): Target namespace
            repo (str): URL of the helm chart repo
            chart (str, optional): Name of the chart to be deployed. Defaults to None.
            values (_type_, optional): Collection of values to override in the chart. Defaults to None.
            yaml_values (_type_, optional): Collection of yaml value files to override chart values. Defaults to None.
        """
        super().__init__('k8sx:component:HelmRelease', name, {}, opts)
        release = Release(
            name,
            ReleaseArgs(
                chart=chart,
                name=name,
                namespace=namespace,
                dependency_update=True,
                create_namespace=True,
                cleanup_on_fail=True,
                atomic=True,
                repository_opts=RepositoryOptsArgs(
                    repo=repo,
                ),
                values=values or self._defaultValues(),
                value_yaml_files=[pulumi.FileAsset(yaml_values)] if yaml_values is not None else None
            ),
            name=name
        )
        if hasService:
            self.service = Service.get(name, Output.concat(release.status.namespace, "/", release.status.name))
            
    def _defaultValues(self):
        """Generate a dictionary of default value.

        Returns:
            Dictionary: Collection of default values for the chart.
        """
        return None;