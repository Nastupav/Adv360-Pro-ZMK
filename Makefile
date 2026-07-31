DOCKER := $(shell { command -v podman || command -v docker; })
.DEFAULT_GOAL := all
PYTHON ?= python3
IMAGE := adv360-zmk-build:local
CONTAINER_USERNS := $(if $(findstring podman,$(DOCKER)),--userns=keep-id:uid=0,)
COMMIT := $(shell git rev-parse --short=12 HEAD 2>/dev/null || printf unknown)
CONFIG_HASH := $(shell $(PYTHON) scripts/firmware_fingerprint.py)
DIRTY_SUFFIX := $(if $(shell git status --porcelain --untracked-files=normal),-dirty,)
ifeq ($(shell uname),Darwin)
SELINUX1 :=
SELINUX2 :=
else
SELINUX1 := :z
SELINUX2 := ,z
endif

.PHONY: all left test verify verify-active clean_firmware clean_image clean

test:
	$(PYTHON) -m unittest discover -s tests -v

verify: test
	$(PYTHON) scripts/verify_workflow.py

verify-active: test
	$(PYTHON) scripts/verify_workflow.py --require-active

all:
	mkdir -p firmware
	$(DOCKER) build --tag $(IMAGE) --file Dockerfile .
	$(DOCKER) run --rm $(CONTAINER_USERNS) \
		-v "$(CURDIR)/firmware:/app/firmware$(SELINUX1)" \
		-v "$(CURDIR)/config:/app/config:ro$(SELINUX2)" \
		-e COMMIT=$(COMMIT) \
		-e CONFIG_HASH=$(CONFIG_HASH) \
		-e DIRTY_SUFFIX=$(DIRTY_SUFFIX) \
		-e BUILD_RIGHT=true \
		$(IMAGE)

left:
	mkdir -p firmware
	$(DOCKER) build --tag $(IMAGE) --file Dockerfile .
	$(DOCKER) run --rm $(CONTAINER_USERNS) \
		-v "$(CURDIR)/firmware:/app/firmware$(SELINUX1)" \
		-v "$(CURDIR)/config:/app/config:ro$(SELINUX2)" \
		-e COMMIT=$(COMMIT) \
		-e CONFIG_HASH=$(CONFIG_HASH) \
		-e DIRTY_SUFFIX=$(DIRTY_SUFFIX) \
		-e BUILD_RIGHT=false \
		$(IMAGE)

clean_firmware:
	rm -f firmware/*.uf2 firmware/SHA256SUMS firmware/build-manifest.json

clean_image:
	$(DOCKER) image rm $(IMAGE)

clean: clean_firmware clean_image
