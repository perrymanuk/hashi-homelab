# Load .env files
include .env 

base_deployments = blackbox-exporter configs coredns docker-registry grafana prometheus telegraf haproxy

help:
	deploy-base					deploys all jobs to nomad
	plan-base						plans deployment of all jobs

.PHONY: deploy-base
deploy-base:
	@echo -n "This will deploy all jobs in this repo. Are you sure? [y/N] " && read ans && [ $${ans:-N} == y ]
	$(foreach var,$(base_deployments), docker run --rm -e NOMAD_TOKEN -e NOMAD_REGION -e ENVIRONMENT -e NOMAD_ADDR -v ${PWD}:/workdir -w /workdir jrasell/levant levant deploy -var-file=/workdir/$(var)/levant.yml -var-file=/workdir/levant/defaults.yml $(var)/nomad.job;)

.PHONY: plan-base
plan-base:
	$(foreach var,$(base_deployments), docker run --rm -e NOMAD_TOKEN -e NOMAD_REGION -e ENVIRONMENT -e NOMAD_ADDR -v ${PWD}:/workdir -w /workdir jrasell/levant levant plan -var-file=/workdir/levant/defaults.yml -var-file=/workdir/$(var)/levant.yml $(var)/nomad.job;)

.PHONY: deploy-job-%
deploy-job-%:
	docker run --rm -e NOMAD_TOKEN -e NOMAD_REGION -e ENVIRONMENT -e NOMAD_ADDR -v ${PWD}:/workdir -w /workdir jrasell/levant levant deploy -var-file=/workdir/levant/defaults.yml -var-file=/workdir/$*/levant.yml $*/nomad.job
