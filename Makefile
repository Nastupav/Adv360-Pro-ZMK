DOCKER := $(shell { command -v podman || command -v docker; })
CONTAINER_USERNS := $(if $(findstring podman,$(DOCKER)),--userns=keep-id:uid=0,)
TIMESTAMP := $(shell date -u +"%Y%m%d%H%M")
COMMIT := $(shell git rev-parse --short HEAD 2>/dev/null)
ifeq ($(shell uname),Darwin)
SELINUX1 :=
SELINUX2 :=
else
SELINUX1 := :z
SELINUX2 := ,z
endif

.PHONY: all left clean_firmware clean_image clean

all:
	mkdir -p firmware
	$(DOCKER) build --tag zmk --file Dockerfile .
	$(DOCKER) run --rm --name zmk $(CONTAINER_USERNS) \
		-v $(PWD)/firmware:/app/firmware$(SELINUX1) \
		-v $(PWD)/config:/app/config:ro$(SELINUX2) \
		-e TIMESTAMP=$(TIMESTAMP) \
		-e COMMIT=$(COMMIT) \
		-e BUILD_RIGHT=true \
		zmk

left:
	mkdir -p firmware
	$(DOCKER) build --tag zmk --file Dockerfile .
	$(DOCKER) run --rm --name zmk $(CONTAINER_USERNS) \
		-v $(PWD)/firmware:/app/firmware$(SELINUX1) \
		-v $(PWD)/config:/app/config:ro$(SELINUX2) \
		-e TIMESTAMP=$(TIMESTAMP) \
		-e COMMIT=$(COMMIT) \
		-e BUILD_RIGHT=false \
		zmk

clean_firmware:
	rm -f firmware/*.uf2 firmware/SHA256SUMS

clean_image:
	$(DOCKER) image rm zmk docker.io/zmkfirmware/zmk-build-arm:stable

clean: clean_firmware clean_image
