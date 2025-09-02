# Hashi-Homelab
<p align="center">
<img width="250" src="homelab.png" />
</p>

### UPDATE - September 2nd 2025

This repo has gone through some major changes since the last update. I've completely reorganized the job structure into 10 clean categories (77 services total now!), added a comprehensive AI/ML stack with Ollama and Open-WebUI, enhanced the monitoring with Loki and Vector for log aggregation, modernized the alertmanager with better persistence and pushover notifications, added weekly docker cleanup automation, redesigned CoreDNS and Traefik for proper HA deployment, and implemented comprehensive Nomad allocation monitoring. The GitHub Actions deployment has been refined with better change detection and the whole thing just runs much more smoothly now. Also added a bunch of new services like smart home integration, personal cloud apps, and storage backends including pgvector for AI workloads, plus a few other bits and bobs that make the whole setup more robust.

### Background

The hashi-homelab was born of a desire to have a simple to maintain but very flexible homelab setup. The main goals were to keep the resources required to run the base lab setup small and to have all of the parts be easily exchangeable. For example I made the main ingress point to the service mesh a DNS round robin. While this isn't a setup I would ever use in production because it isn't the most dynamically flexible in terms of service discovery, it is however a very easy setup and if you want to launch a new mesh you just give it the Consul name `service-mesh` and run the job and then bam! Bob's your uncle.  

`make deploy-base` will deploy coredns, docker-registry and haproxy - these are needed for everything else to work but aside from these you can pick and choose what to deploy with `make deploy-SERVICE_NAME` to deploy any of the 77 services organized across 10 categories. `make deploy-prometheus` or `make deploy-ollama` for example. You can also target specific datacenters with `make dc1-traefik` or `make all-postgres`.

The whole thing is organized much better now with services grouped into logical categories like ai-ml, media-stack, smart-home, observability, etc. Makes it way easier to find what you're looking for and deploy related services together.

In the future I would like to provide a ready to boot image for a raspberry pi where you can run all of this as the resources needed are really minimal. With just the basics you can get away with one pi4 4gb model with plenty of room to spare.

### Core Components:

* **Scheduler**: Nomad *...with proper allocation monitoring now*
* **Service Catalog/Registry**: Consul  
* **Service Mesh**: Traefik *...redesigned for HA deployment, much more robust*
* **VPN**: Tailscale *...can't say enough good things about tailscale, its integral for my homelab now*
* **DNS**: CoreDNS *...now with HA setup and proper failover*
* **Keepalived**: Assign a floating IP for DNS to not lose it if a node goes down
* **Monitoring**: Prometheus, Alertmanager, Telegraf, Blackbox-exporter, and Grafana *...plus Loki and Vector for log aggregation*  
* **Container Registry**: Docker-Registry *...because sometimes you don't want to rely on Docker Hub being up*  
* **AI/ML**: Ollama for local LLM serving, Open-WebUI for chat interface, LiteLLM for API compatibility
* **Vector Database**: PostgreSQL with pgvector extension for AI/ML vector embeddings storage and similarity search
* **Storage**: NFS and iSCSI CSI plugins for persistent storage across the cluster

### Service Categories (77 total):

* **ai-ml** (8): ollama, open-webui, litellm, cognee, crawl4ai, manyfold, paperless-ai, pgvector-client
* **core-infra** (13): coredns, traefik, haproxy, keepalived, tailscale, github-runner, csi plugins, etc.
* **media-stack** (16): plex, sonarr, radarr, lidarr, sabnzbd, qbittorrent, overseerr, navidrome, etc.
* **personal-cloud** (4): nextcloud, bitwarden, paperless, radicale
* **smart-home** (5): home-assistant, deconz, zigbee2mqtt, mqtt, owntracks-recorder  
* **observability** (7): prometheus, grafana, alertmanager, loki, vector, telegraf, blackbox-exporter
* **storage-backends** (9): postgres, pgvector, redis, mariadb, neo4j, qdrant, docker-registry, etc.
* **web-apps** (5): heimdall, wordpress, firecrawl, alertmanager-dashboard, www
* **misc** (7): gitea, uploader, murmur, octoprint, adb, linuxgsm, gcp-dns-updater
* **system** (3): docker-cleanup, volumes

### Setup

You need to have Nomad and Consul already running, a simple setup with the -dev flag will suffice for testing but you'll want a proper cluster for real usage. If don't already have a Nomad and Consul cluster, there are some excellent guides here...  
https://www.nomadproject.io/guides/install/production/deployment-guide.html  
https://learn.hashicorp.com/consul/datacenter-deploy/deployment-guide  

There are also some files in the `config` folder to help you get started and also one with some services to announce so the Consul and Nomad UI are available over the service mesh.

This repo relies on a `.envrc` file and direnv installed or setting the environment variables manually.
There is an `envrc` example file located in the repo that you can fill in and move to `.envrc`


The secret values from the `.envrc` also need to be put into your github secrets if you plan on deploying via the automated workflow. You can use `make sync-github-secrets` to sync them all at once which is pretty handy.

Once this is done, you simply run a `make deploy-base` and point your DNS to resolve via one of the Nomad nodes' IP address.  

One of the more specific parts of the setup that you may need to adjust is I use several NFS mounts to provide persistent storage mounted on each client at `/home/shared` for configs and `/home/media` for images, video, audio, etc. Depending on which parts of this you are planning to deploy you will just need to adjust this persistent storage to meet the setup of your clients. The CSI plugins help make this more flexible now.

Services are exposed by their task name in the nomad job and whatever you configure your TLD to be in the `.envrc`. The whole thing works really well with the automated GitHub Actions deployment now - just push changes and they get deployed automatically to your cluster. This requires tailscale for the GitHub Actions to connect to your cluster.
