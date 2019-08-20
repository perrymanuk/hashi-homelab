# Hashi-Homelab
<img width="250" src="homelab.png" />

The hashi-homelab was born of a desire to have a simple to maintain but very flexible homelab setup. The main goals were to keep the resources required to run the base lab setup small and to have all of the parts be easily exchangeable. For example I made the main ingress point to the service mesh a dns round robin. While This isn't a setup I would ever use in production because it isn't the most dynamically flexible in terms of service discovery it is however a very easy setup and if you want to launch a new mesh you just give it the consul name `service-mesh` and run the job and the bam bob's your uncle.

### Componets:

Scheduler - Nomad  
Service Catalog/Registry - Consul  
Service Mesh - HAProxy2  
*the decicision was between haproxy and nginx as they are both the lightest weight options however since haproxy2 now supports retry logic and native prometheus metrics I thought I would give it a try.  
DNS - CoreDNS  
Monitoring - Prometheus, Alertmanager, Telegraf, Blackbox-exporter, and Grafana  
Container Registry - Docker-Registry  
*because sometimes you don't want to rely on dockerhub being up  

### Setup

You need to have Nomad and Consul already running, a simple setup with the -dev flag with suffice. If don't already have a Nomad and Consul cluster there are some excellent guides here...  
https://www.nomadproject.io/guides/install/production/deployment-guide.html  
https://learn.hashicorp.com/consul/datacenter-deploy/deployment-guide  

There are also some files in the `config` folder to help you get started and also one with some services to announce so the consul and nomad ui are available over the service mesh.

This repo relies on a .envrc file and direnv installed or setting the environment variables manually
```
export NOMAD_ADDR=''
export NOMAD_TOKEN=''
export VAULT_TOKEN=''
```
`.envrc` example

once this is done you simply run a `make deploy-all` and point your dns to resolve via one of the nomad nodes ip address.  
*two of the jobs `grafana` and `docker-registry` use my nfs mount path of `/mnt/cucumber/nomad` you can change this to your own nfs mount or if you don't have one you can pint these jobs to a particular node to have persistant storage.  

services are exposed via http://$service_name.homelab after you point your dns to a nomad node.  
For example you can go to http://prometheus.homelab to visit the prometheus-ui  
http://nomad-ui.homelab to view the nomad ui and explore the jobs  
http://consul-agent.homelab import some of the dashboards to explore around more.  
http://grafana.homelab and import some of the dashboards from the repo to view your metrics  



consul domain is switched to .home to provide seperation from the traffic lb setup 
