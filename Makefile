# Load .env files
#include .envrc

include ./.bootstrap.mk

base_deployments = coredns docker-registry haproxy

#help:

.PHONY: dc1-%
dc1-%:##........Deploy specific job from sub folder
	nomad job run -var datacenters='["dc1"]' $*/nomad.job

.PHONY: all-%
all-%:##........Deploy specific job from sub folder
	nomad job run -var datacenters='["dc1", "hetzner"]' $*/nomad.job

.PHONY: deploy-%
deploy-%:##........Deploy specific job from sub folder
	nomad job run $*/nomad.job

.PHONY: deploy-base
deploy-base:##.....Deploys all jobs to nomad
	@echo -n "This will deploy all jobs in this repo. Are you sure? [y/N] " && read ans && [ $${ans:-N} == y ]
	$(foreach var,$(base_deployments), nomad job run -var datacenters='["dc1"]' $*/nomad.job $(var)/nomad.job;)

.PHONY: sslkeys
sslkeys:##.........Generate certs if you have SSL enabled
	consul-template -config ssl/consul-template.hcl -once -vault-renew-token=false

.PHONY: ssl-browser-cert
ssl-browser-cert:##.........Generate certs if you have SSL enabled
	sudo openssl pkcs12 -export -out browser_cert.p12 -inkey ssl/hetzner/server-key.pem -in ssl/hetzner/server.pem -certfile ssl/hetzner/nomad-ca.pem
