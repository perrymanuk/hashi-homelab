# Load .env files
include .env 

deployments = blackbox-exporter configs coredns docker-registry grafana prometheus telegraf haproxy

help:
	deploy-all					deploys all jobs to nomad
	plan-all						plans deployment of all jobs

.PHONY: deploy-all
deploy-all:
	@echo -n "This will deploy all jobs in this repo. Are you sure? [y/N] " && read ans && [ $${ans:-N} == y ]
	$(foreach var,$(deployments), docker run --rm -e NOMAD_TOKEN -e NOMAD_REGION -e ENVIRONMENT -e NOMAD_ADDR -v ${PWD}:/workdir -w /workdir jrasell/levant levant deploy -var-file=/workdir/levant/defaults.yml $(var)/nomad.job;)

.PHONY: plan-all
plan-all:
	$(foreach var,$(deployments), docker run --rm -e NOMAD_TOKEN -e NOMAD_REGION -e ENVIRONMENT -e NOMAD_ADDR -v ${PWD}:/workdir -w /workdir jrasell/levant levant plan -var-file=/workdir/levant/defaults.yml $(var)/nomad.job;)

