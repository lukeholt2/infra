from components.helm_release import HelmRelease

def deploy_tools(target_namespace: str, runner_config):
    runner = HelmRelease("gitlab-runner", 
                    target_namespace, 
                    "https://charts.gitlab.io", 
                    chart="gitlab-runner",
                    values={
                        "gitlabUrl": runner_config['gitlabUrl'],
                        "runnerToken": runner_config['runnerToken'],
                        "rbac": { "create": True },
                        "certsSecretName": "gitlab-tls",
                    },
                    yaml_values="./configs/gitlab-runner/config.yml",
                    hasService=False
                )