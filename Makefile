# Load .env files
include .env 

deployments = blackbox-exporter configs coredns docker-registry grafana prometheus telegraf haproxy

help:
	deploy-all					deploys all jobs to nomad
	plan-all						plans deployment of all jobs

.PHONY: deploy-all
deploy-all:
	$(foreach var,$(deployments),nomad run $(var)/nomad.job;)

.PHONY: plan-all
plan-all:
	@echo -n "This will deploy all jobs in this repo. Are you sure? [y/N] " && read ans && [ $${ans:-N} == y ]
	$(foreach var,$(deployments),nomad job plan $(var)/nomad.job;)

