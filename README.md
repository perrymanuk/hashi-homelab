# Hashi-Homelab
<p align="center">
<img width="250" src="homelab.png" />
</p>

### UPDATE - June 10th 2023

This repo has gone through some recent changes, I introduced the usage of tailscale, levant has been replaced by hcl2, replaced haproxy with traefik, local deployments via the make command have been extended to include "gitops" deployments via github actions and custom runners, added keepalived to make dns setup more robust, removed the usage of vault and replaced it with github secrets to avoid setting up an auto-unseal for vault as the other alternative for giving the cluster the ability to recover from a full power outtage on its own, and a few other smaller bits and bobs.

### Background

The hashi-homelab was born of a desire to have a simple to maintain but very flexible homelab setup. The main goals were to keep the resources required to run the base lab setup small and to have all of the parts be easily exchangeable. For example I made the main ingress point to the service mesh a DNS round robin. While this isn't a setup I would ever use in production because it isn't the most dynamically flexible in terms of service discovery, it is however a very easy setup and if you want to launch a new mesh you just give it the Consul name `service-mesh` and run the job and then bam! Bob's your uncle.  

`make base` will deploy coredns, docker-registry and haproxy these are needed for everything else to work but aside from these you can pick and choose what to deploy with `make deploy-FOLDER_NAME` to deploy any of the jobs from the included subfolders. `make deploy-prometheus` for example.

In the future I would like to provide a ready to boot image for a raspberry pi where you can run all of this as the resources needed are really minimal. With just the basics you can get away with one pi4 4gb model with plenty of room to spare.

### Core Componets:

* Scheduler: Nomad  
* Service Catalog/Registry: Consul  
* Service Mesh: Traefik
* VPN: Tailscale *...can't say enough good things about tailscale, its integral for my homelab now*
* DNS: CoreDNS 
* Keepalived: Assign a floating IP for DNS to not loose it if a node goes down.
* Monitoring: Prometheus, Alertmanager, Telegraf, Blackbox-exporter, and Grafana  
* Container Registry: Docker-Registry  *...because sometimes you don't want to rely on Docker Hub being up*  
* Vector Database: PostgreSQL with pgvector extension for AI/ML vector embeddings storage and similarity search

### Setup

**This is all out of date now and needs to be updated as the setup requires the usage of tailscale or you need to modify each job you want to deploy**

You need to have Nomad and Consul already running, a simple setup with the -dev flag will suffice. If don't already have a Nomad and Consul cluster, there are some excellent guides here...  
https://www.nomadproject.io/guides/install/production/deployment-guide.html  
https://learn.hashicorp.com/consul/datacenter-deploy/deployment-guide  

There are also some files in the `config` folder to help you get started and also one with some services to announce so the Consul and Nomad UI are available over the service mesh.

This repo relies on a `.envrc` file and direnv installed or setting the environment variables manually.
There is an `envrc` example file located in the repo that you can fill in and move to `.envrc`

The secret values from the `.envrc` also need to be put into your github secrets if you plan on deploying via the workflow included in this repo

Once this is done, you simply run a `make deploy-base` and point your DNS to resolve via one of the Nomad nodes' IP address.  

One of the more specific parts of the setup that you may need to adjust is I use several NFS mounts to provide persistant storage mounted on each client at `/home/shared` for configs and `/home/media` for images, video, audio, etc. Depending on which parts of this you are planning to deploy you will just need to adjust this persistant storage to meet the setup of your clients.

Services are exposed by their task name in the nomad job and whatever you configure your TLD to be in the `.envrc`. Currently I have this setup to deploy an instance of traefik to a single VM in a public cloud where I use it to route to my services I want to expose via [tailscale](http://www.tailscale.com). 

 
