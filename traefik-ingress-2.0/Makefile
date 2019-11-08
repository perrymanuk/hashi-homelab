export VERSION_TAG=$(shell git rev-parse --short HEAD)
export JOB_NAME=tcs-$(shell basename $PWD)
# We need a way to fetch the current docker file from our documentation and build it hear, something like `curl docker.tcs.trv.cloud/tcs/blackbox/Dockerfile
#
#
#.PHONY: build
#build:
#	docker build -t $(TRV_DOCKER_IMAGE) .
#
#.PHONY: push
#push:
#	docker push $(TRV_DOCKER_IMAGE)
#	docker tag $(TRV_DOCKER_IMAGE) $(TRV_IMAGE_WITH_VERSION)
#	docker push $(TRV_IMAGE_WITH_VERSION)
#
#.PHONY: open
open:
	open http://$(JOB_NAME).prod.dus.tcs.trv.cloud/

.PHONY: nomadui
nomadui:
	open http://nomad-ui.tcs.trv.cloud/nomad/europe/jobs/${JOB_NAME}/info

.PHONY: stop
stop: ## Stop job on Nomad
	nomad stop -purge --region=$(TRV_REGION) $(JOB_NAME)

.PHONY: status
status: ## Show current status of Nomad job
	nomad status --region=$(TRV_REGION) $(JOB_NAME)

.PHONY: deploy-%
deploy-%: ## Deploy the containers to Nomad
ifndef FORCE_DEPLOY
	@echo -n "This will deploy to Nomad ($*). Are you sure? [y/N] " && read ans && [ $${ans:-N} == y ]
endif
	@docker run --rm -e NOMAD_TOKEN -e NOMAD_REGION -e ENVIRONMENT -e NOMAD_ADDR=$(NOMAD_ADDR) -v ${PWD}:/workdir -w /workdir jrasell/levant levant deploy -ignore-no-changes -var-file=/workdir/deployments/$*.yml nomad.job

.PHONY: render-%
render-%: ## Deploy the containers to Nomad
	@docker run --rm -e TRV_CACHE_IMAGE_WITH_VERSION -e NOMAD_TOKEN -e NOMAD_REGION -e ENVIRONMENT -e NOMAD_ADDR -v ${PWD}:/workdir -w /workdir jrasell/levant levant render -var-file=/workdir/deployments/$*.yml nomad.job
