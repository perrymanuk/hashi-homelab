# Load .env files
#include .envrc

base_deployments = coredns docker-registry haproxy

help:
	deploy-base					deploys all jobs to nomad
	plan-base						plans deployment of all jobs
	deploy-FOLDER_NAME			deploy specific job from sub folder

.PHONY: deploy-base
deploy-base:
	@echo -n "This will deploy all jobs in this repo. Are you sure? [y/N] " && read ans && [ $${ans:-N} == y ]
	$(foreach var,$(base_deployments), docker run --rm -e NOMAD_TOKEN -e NOMAD_REGION -e ENVIRONMENT -e NOMAD_ADDR -v ${PWD}:/workdir -w /workdir jrasell/levant deploy -vault -var-file=/workdir/levant/defaults.yml $(var)/nomad.job;)

.PHONY: plan-base
plan-base:
	$(foreach var,$(base_deployments), docker run --rm -e NOMAD_TOKEN -e NOMAD_REGION -e ENVIRONMENT -e NOMAD_ADDR -v ${PWD}:/workdir -w /workdir jrasell/levant plan -var-file=/workdir/levant/defaults.yml $(var)/nomad.job;)

.PHONY: deploy-%
deploy-%:
	docker run --rm --add-host=server.europe.nomad:88.99.163.75 -e VAULT_TOKEN -e NOMAD_CACERT -e NOMAD_CLIENT_CERT -e NOMAD_CLIENT_KEY -e NOMAD_TOKEN -e NOMAD_REGION -e ENVIRONMENT -e NOMAD_ADDR -v ${PWD}:/workdir -w /workdir jrasell/levant deploy -vault -var-file=/workdir/levant/defaults.yml $*/nomad.job

.PHONY: vault
vault:
	docker run -e VAULT_ADDR -e VAULT_TOKEN -v ~/git/github/hashi-homelab/levant/vault:/vault perrymanuk/vault-wrapper /usr/bin/vault-sync sync --sync-full -c /vault/test.yaml

.PHONY: sslkeys
sslkeys:
	consul-template -config ssl/consul-template.hcl -once -vault-renew-token=false

.PHONY: vault
vault:
	docker run -e VAULT_ADDR -e VAULT_TOKEN -v ~/git/github/hashi-homelab/vault:/vault perrymanuk/vault-wrapper /usr/bin/vault-sync sync --sync-full -c /vault/test.yaml
