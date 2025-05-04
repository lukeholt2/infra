import pulumi
from components.ingress import create_controller, register_ingress
from components.helm_release import HelmRelease
from apps.expenseapp import ExpenseApp
from apps.vaultwarden import VaultWarden
from apps.tools import deploy_tools

config = pulumi.Config();
target_namespace = 'homelab'

create_controller(target_namespace);
frigate = HelmRelease("frigate", 
                    target_namespace, 
                    "https://blakeblackshear.github.io/blakeshome-charts", 
                    chart="frigate",
                    values={
                        'env':{
                            'FRIGATE_RTSP_PASSWORD': config.require_secret('frigate_pass'),
                            'FRIGATE_RTSP_PASSWORD2': config.require_secret('frigate_pass2')
                        }
                    },
                    yaml_values="./configs/frigate/config.yml"
                )
register_ingress('frigate', 
                target_namespace, 
                "frigate.internal.oasis.com", 
                [frigate.service], 
                [''])

homer = HelmRelease("homer", 
                    target_namespace, 
                    "https://djjudas21.github.io/charts/", 
                    chart="homer", 
                    values={
                        'env':{
                            'PIHOLE_KEY': config.require_secret('pihole_key')
                        }
                    },
                    yaml_values="./configs/homer/config.yml"
        )
register_ingress('homer', target_namespace, 'homer.internal.oasis.com', [homer.service], [''])


expense_config = config.require_object('expenseapp')
ExpenseApp(target_namespace, expense_config['url'], expense_config['ui_version'], expense_config['api_version'])

runner_config = config.require_object('gitlab-runner')
deploy_tools(target_namespace, runner_config)

vault_config = config.require_object('vaultWarden')
VaultWarden('vault', target_namespace, vault_config['domain'])