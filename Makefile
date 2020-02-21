# Load .env files
#include .envrc

include ./.bootstrap.mk

base_deployments = coredns docker-registry haproxy

#help:

.PHONY: deploy-base
deploy-base:##.....Deploys all jobs to nomad
	@echo -n "This will deploy all jobs in this repo. Are you sure? [y/N] " && read ans && [ $${ans:-N} == y ]
	$(foreach var,$(base_deployments), docker run --rm -e NOMAD_TOKEN -e NOMAD_REGION -e ENVIRONMENT -e NOMAD_ADDR -v ${PWD}:/workdir -w /workdir jrasell/levant deploy -vault -var-file=/workdir/levant/defaults.yml $(var)/nomad.job;)

.PHONY: plan-base
plan-base:##.......Plans deployment of all jobs
	$(foreach var,$(base_deployments), docker run --rm -e NOMAD_TOKEN -e NOMAD_REGION -e ENVIRONMENT -e NOMAD_ADDR -v ${PWD}:/workdir -w /workdir jrasell/levant plan -var-file=/workdir/levant/defaults.yml $(var)/nomad.job;)

.PHONY: deploy-%
deploy-%:##........Deploy specific job from sub folder
	docker run --rm -e VAULT_TOKEN -e NOMAD_CACERT -e NOMAD_CLIENT_CERT -e NOMAD_CLIENT_KEY -e NOMAD_TOKEN -e NOMAD_REGION -e ENVIRONMENT -e NOMAD_ADDR -v ${PWD}:/workdir -w /workdir jrasell/levant deploy -vault -var-file=/workdir/levant/defaults.yml $*/nomad.job

.PHONY: vault
vault:##...........Sync vault secrets from repo
	docker run -e VAULT_ADDR -e VAULT_TOKEN -v ~/git/github/hashi-homelab/levant/vault:/vault perrymanuk/vault-wrapper /usr/bin/vault-sync sync --sync-full -c /vault/secrets.yaml

.PHONY: sslkeys
sslkeys:##.........Generate certs if you have SSL enabled
	consul-template -config ssl/consul-template.hcl -once -vault-renew-token=false

