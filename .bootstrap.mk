export VERSION_TAG=$(shell git rev-parse --short HEAD)
export JOB_NAME=$(shell basename $PWD)

dash-split = $(word $2,$(subst -, ,$1))
dash-1 = $(call dash-split,$*,1)
dash-2 = $(call dash-split,$*,2)

help:##............Show this help.
	@echo ""
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##//' | sed 's/^/    /'
	@echo ""
	@echo ""
