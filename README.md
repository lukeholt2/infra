# Homelab

Collection of configurations / scripts used to deploy my internal homelab, all (theoretically) automated via `ansible` and `pulumi`. The repo is broken into two sections, [infra](/infra) is the collection of `ansible` playbooks and roles used in machine setup, and [`k3s`](/k3s) (as the name implies) is responsible for handling the internal `K3s` cluster.

## Configuring the Infrastructure

See the `infra` [README](/infra/README.md) for running the setup scripts.

## Building the K3s cluster

The current cluster is built using [`K3s`](https://docs.k3s.io/) and deployed using the [k3s-ansible](https://github.com/k3s-io/k3s-ansible/tree/master) project. To deploy the cluster follow the instructions [here](https://docs.k3s.io/) using the inventory and variables found in [inventory](/inventory)

## Deploying Homelab K3s Stack

Deploying homelab services to the K3s cluster is handled by [pulumi](https://www.pulumi.com/).

First, install the `pulumi` cli: 

```script
curl -fsSL https://get.pulumi.com | sh
```

Then setup the virtual environment:

```script
python -m venv venv


source venv/bin/activate


pip install -r requirements.txt
```


Finally, deploy the stack :fire:

`pulumi up -s prod -f`