# config variable
DOCKER_REPO ?= ghcr.io/citusdata
SHA_SUFFIX := $(shell git rev-parse --short HEAD)
ifeq ($(strip $(SHA_SUFFIX)),)
$(error Failed to determine git short SHA)
endif

# auto generated variables
ifdef RELEASE
	TAG_SUFFIX := -v${SHA_SUFFIX}
else
	TAG_SUFFIX := -dev-${SHA_SUFFIX}
endif

VERSIONS_FILE := ../../versions.json

# all postgres versions we test against
PG_VERSIONS := $(shell jq -er '.postgres_ci | to_entries | sort_by(.key | tonumber) | map(.value | if (type == "string" and length > 0) then . else error("invalid postgres_ci version") end) | join(" ")' $(VERSIONS_FILE) || echo __JQ_ERR__)
ifneq ($(filter __JQ_ERR__,$(PG_VERSIONS)),)
$(error Failed to read postgres_ci from $(VERSIONS_FILE) (is jq installed?))
endif
ifeq ($(strip $(PG_VERSIONS)),)
$(error Empty postgres_ci in $(VERSIONS_FILE))
endif

PG_UPGRADE_TESTER_VERSION := $(shell echo ${PG_VERSIONS}|tr ' ' '-'|sed 's/~//g')

STYLE_CHECKER_TOOLS_VERSION := $(shell jq -er '.style_checker_tools_version | if (type == "string" and length > 0) then . else error("invalid style_checker_tools_version") end' $(VERSIONS_FILE) || echo __JQ_ERR__)
ifneq ($(filter __JQ_ERR__,$(STYLE_CHECKER_TOOLS_VERSION)),)
$(error Failed to read style_checker_tools_version from $(VERSIONS_FILE))
endif

# Upgrade tests for the PG major versions listed in upgrade_test_pg
CITUS_UPGRADE_PG_VERSIONS := $(shell jq -er '. as $$v | (.upgrade_test_pg // []) | map($$v.postgres_ci[.] // error("unknown upgrade_test_pg major: " + .)) | join(" ")' $(VERSIONS_FILE) || echo __JQ_ERR__)
ifneq ($(filter __JQ_ERR__,$(CITUS_UPGRADE_PG_VERSIONS)),)
$(error Failed to resolve upgrade_test_pg from $(VERSIONS_FILE))
endif

# Function to get Citus versions for a specific PG major version
get_citus_versions = $(shell jq -r --arg m "$(1)" '(.upgrade_from[$$m] // []) | join(" ")' $(VERSIONS_FILE))

.PHONY: print-tag-suffix
print-tag-suffix:
	@echo "${TAG_SUFFIX}"

# code below creates targets for all postgres versions in PG_VERSIONS
define make-image-targets
# $1 = PG_VERSION
# $2 = PG_MAJOR
# $3 = PG_VERION_CLEAN

build-extbuilder-$1:
	docker build \
		extbuilder/ \
		-f extbuilder/Dockerfile \
		--build-arg=PG_VERSION=$1 \
		--build-arg=PG_MAJOR=$2 \
		--tag=${DOCKER_REPO}/extbuilder:$3${TAG_SUFFIX}

build-all:: build-extbuilder-$1

build-extbuilder-all:: build-extbuilder-$1

push-extbuilder-$1: build-extbuilder-$1
	docker push ${DOCKER_REPO}/extbuilder:$3${TAG_SUFFIX}

push-all:: push-extbuilder-$1

push-extbuilder-all:: push-extbuilder-$1

build-exttester-$1:
	docker build \
		exttester/ \
		-f exttester/Dockerfile \
		--build-arg=PG_VERSION=$1 \
		--build-arg=PG_MAJOR=$2 \
		--build-arg=PG_VERSION_CLEAN=$3 \
		--tag=${DOCKER_REPO}/exttester:$3${TAG_SUFFIX}

build-all:: build-exttester-$1

build-exttester-all:: build-exttester-$1

push-exttester-$1: build-exttester-$1
	docker push ${DOCKER_REPO}/exttester:$3${TAG_SUFFIX}

push-all:: push-exttester-$1

push-exttester-all:: push-exttester-$1

build-failtester-$1:
	docker build \
		failtester/ \
		-f failtester/Dockerfile \
		--build-arg=PG_VERSION=$1 \
		--build-arg=PG_MAJOR=$2 \
		--tag=${DOCKER_REPO}/failtester:$3${TAG_SUFFIX}

build-all:: build-failtester-$1

build-failtester-all:: build-failtester-$1

push-failtester-$1: build-failtester-$1
	docker push ${DOCKER_REPO}/failtester:$3${TAG_SUFFIX}

push-all:: push-failtester-$1

push-failtester-all:: push-failtester-$1
endef

# call make-image-targets($PG_VERSION, $PG_MAJOR) for every version in PG_VERSIONS
$(foreach element,$(PG_VERSIONS),$(eval $(call make-image-targets,$(element),$(shell echo $(element) | awk -F'[^0-9]*' '/[0-9]/ { print $$1 }'),$(shell echo $(element) | sed 's/~//'))))

define make-citus-upgrage-targets
# $1 = PG_VERSION
# $2 = PG_MAJOR
# $3 = PG_VERION_CLEAN

build-citusupgradetester-$1:
	docker build \
		citusupgradetester/ \
		-f citusupgradetester/Dockerfile \
		--build-arg=PG_VERSION=$1 \
		--build-arg=PG_MAJOR=$2 \
		--build-arg=CITUS_VERSIONS="$(call get_citus_versions,$2)" \
		--tag=${DOCKER_REPO}/citusupgradetester:$3${TAG_SUFFIX}

build-all:: build-citusupgradetester-$1
build-citusupgradetester-all:: build-citusupgradetester-$1

push-citusupgradetester-$1: build-citusupgradetester-$1
	docker push ${DOCKER_REPO}/citusupgradetester:$3${TAG_SUFFIX}

push-all:: push-citusupgradetester-$1
push-citusupgradetester-all:: push-citusupgradetester-$1
endef
$(foreach element,$(CITUS_UPGRADE_PG_VERSIONS),$(eval $(call make-citus-upgrage-targets,$(element),$(shell echo $(element) | awk -F'[^0-9]*' '/[0-9]/ { print $$1 }'),$(shell echo $(element) | sed 's/~//'))))


# pg upgrade image is 1 global image
build-pgupgradetester:
	docker build \
		pgupgradetester/ \
		-f pgupgradetester/Dockerfile \
		--build-arg=PG_VERSIONS="${PG_VERSIONS}" \
		--tag=${DOCKER_REPO}/pgupgradetester:${PG_UPGRADE_TESTER_VERSION}${TAG_SUFFIX}

build-all:: build-pgupgradetester

push-pgupgradetester-all: build-pgupgradetester
	docker push ${DOCKER_REPO}/pgupgradetester:${PG_UPGRADE_TESTER_VERSION}${TAG_SUFFIX}

push-all:: push-pgupgradetester-all

# style checker image is 1 global image
build-stylechecker:
	docker build \
		stylechecker/ \
		-f stylechecker/Dockerfile \
		--build-arg=TOOLS_VERSION="${STYLE_CHECKER_TOOLS_VERSION}" \
		--tag=${DOCKER_REPO}/stylechecker:${STYLE_CHECKER_TOOLS_VERSION}${TAG_SUFFIX}

build-all:: build-stylechecker

push-stylechecker-all: build-stylechecker
	docker push ${DOCKER_REPO}/stylechecker:${STYLE_CHECKER_TOOLS_VERSION}${TAG_SUFFIX}

push-all:: push-stylechecker-all
