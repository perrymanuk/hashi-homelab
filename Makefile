# Load .env files
#include .envrc

include ./.bootstrap.mk

# Define base deployments using their service names
base_deployments = coredns docker-registry haproxy

#help: # Placeholder for potential future help generation

# Find the nomad job file for a given service name ($1) within nomad_jobs/ structure
# Usage: $(call find_job_file, service_name)
# Example: $(call find_job_file, coredns) -> nomad_jobs/core-infra/coredns/coredns.job (or .nomad)
find_job_file = $(shell find nomad_jobs/ -mindepth 2 -maxdepth 3 -type f \( -name '$1.job' -o -name '$1.nomad' \) -print -quit)

.PHONY: dc1-%
dc1-%: ## Deploy specific job to dc1 (searches within nomad_jobs/ structure)
	@JOB_FILE=$(call find_job_file,$*); \
	if [ -z "$$JOB_FILE" ]; then \
		echo "Error: Could not find nomad job file for '$*' in nomad_jobs/."; \
		exit 1; \
	fi; \
	echo "Found job file: $$JOB_FILE"; \
	nomad job run -var datacenters='["dc1"]' $$JOB_FILE

.PHONY: all-%
all-%: ## Deploy specific job to all DCs (searches within nomad_jobs/ structure)
	@JOB_FILE=$(call find_job_file,$*); \
	if [ -z "$$JOB_FILE" ]; then \
		echo "Error: Could not find nomad job file for '$*' in nomad_jobs/."; \
		exit 1; \
	fi; \
	echo "Found job file: $$JOB_FILE"; \
	nomad job run -var datacenters='["dc1", "hetzner"]' $$JOB_FILE

.PHONY: deploy-%
deploy-%: ## Deploy specific job (searches within nomad_jobs/ structure)
	@JOB_FILE=$(call find_job_file,$*); \
	if [ -z "$$JOB_FILE" ]; then \
		echo "Error: Could not find nomad job file for '$*' in nomad_jobs/."; \
		exit 1; \
	fi; \
	echo "Found job file: $$JOB_FILE"; \
	nomad job run $$JOB_FILE

.PHONY: deploy-base
deploy-base: ## Deploys base jobs (coredns, docker-registry, haproxy) to dc1
	@echo "Deploying base services to dc1: $(base_deployments)"
	$(foreach var,$(base_deployments), \
	    @JOB_FILE=$$(call find_job_file,$(var)); \
	    if [ -z "$$JOB_FILE" ]; then \
	        echo "Error: Could not find nomad job file for base deployment '$(var)' in nomad_jobs/."; \
	        exit 1; \
	    fi; \
	    echo "Deploying $(var) from $$JOB_FILE..."; \
	    nomad job run -var datacenters='["dc1"]' $$JOB_FILE; \
	)

.PHONY: sslkeys
sslkeys: ## Generate certs if you have SSL enabled
	consul-template -config ssl/consul-template.hcl -once -vault-renew-token=false

.PHONY: ssl-browser-cert
ssl-browser-cert: ## Generate browser cert if you have SSL enabled
	sudo openssl pkcs12 -export -out browser_cert.p12 -inkey ssl/hetzner/server-key.pem -in ssl/hetzner/server.pem -certfile ssl/hetzner/nomad-ca.pem

.PHONY: sync-github-secrets
sync-github-secrets: ## Sync NOMAD_VAR variables from .envrc to GitHub secrets using gh CLI
	@echo "Syncing NOMAD_VAR variables from .envrc to GitHub secrets..."
	@bash -c 'source .envrc && env | grep "^NOMAD_VAR_" | while IFS="=" read -r name value; do \
		echo "Setting $$name"; \
		echo "$$value" | gh secret set "$$name"; \
	done'
	@echo "✅ All NOMAD_VAR secrets synced to GitHub"

.PHONY: build-update-metadata
build-update-metadata: ## Build the update-metadata Docker image
	@echo "Building update-metadata Docker image..."
	# Assumes update-metadata is in docker_images/update-metadata/
	docker build --platform linux/amd64 -t update-metadata:latest docker_images/update-metadata/

.PHONY: build-gcp-dns-updater
build-gcp-dns-updater: ## Build the gcp-dns-updater Docker image
	@echo "Building gcp-dns-updater Docker image..."
	# Assumes gcp-dns-updater is in docker_images/gcp-dns-updater/
	docker build --platform linux/amd64 -t docker.$$NOMAD_VAR_tld/gcp-dns-updater:latest docker_images/gcp-dns-updater/

# Example deployment target for gcp-dns-updater (if needed, uncomment and adjust)
#.PHONY: deploy-gcp-dns-updater
#deploy-gcp-dns-updater: ## Deploy gcp-dns-updater job using generic target
#	$(MAKE) deploy-gcp-dns-updater
