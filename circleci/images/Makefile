# config variable
DOCKER_REPO ?= ghcr.io/citusdata
SHA_SUFFIX := $(shell git rev-parse --short HEAD)

# Upstream postgres git ref used to source-build PG19 (which is unreleased
# and therefore not available via apt.postgresql.org). Override at build
# time, e.g. `make PG19_SOURCE_REF=master push-extbuilder-19devel`.
PG19_SOURCE_REF ?= 43649b6a53e9b3964e921cc962f5c977bce688fd

# auto generated variables
ifdef RELEASE
	TAG_SUFFIX := -v${SHA_SUFFIX}
else
	TAG_SUFFIX := -dev-${SHA_SUFFIX}
endif

# all postgres versions we test against
PG_VERSIONS=$(shell cat PG_VERSIONS|cut -c 6-|tr '\n' ' ' )

PG_UPGRADE_TESTER_VERSION=$(shell echo ${PG_VERSIONS}|tr ' ' '-'|sed 's/~//g')

STYLE_CHECKER_TOOLS_VERSION=0.8.33

# Upgrade tests for the PG major versions from PG_VERSIONS file.
# PG19 is excluded because no Citus release supports it yet; filter it
# out by name so reordering PG_VERSIONS does not silently change which
# major is dropped.
CITUS_UPGRADE_PG_VERSIONS=$(shell grep -v '^PG19=' PG_VERSIONS|cut -c 6-|tr '\n' ' ')
# 12.1.10 is the latest release of Citus 12 when the test is expanded to cover Citus 12
CITUS_UPGRADE_VERSIONS_16=v12.1.12
# Latest minor version of Citus 13
CITUS_UPGRADE_VERSIONS_17=v13.2.2
# Latest minor version of Citus 14
CITUS_UPGRADE_VERSIONS_18=v14.0.1

# Function to get Citus versions for a specific PG major version
get_citus_versions = $(CITUS_UPGRADE_VERSIONS_$(1))

# Function to get the last Citus version for a specific PG major version
get_last_citus_version = $(lastword $(CITUS_UPGRADE_VERSIONS_$(1)))

# code below creates targets for all postgres versions in PG_VERSIONS
define make-image-targets
# $1 = PG_VERSION
# $2 = PG_MAJOR
# $3 = PG_VERSION_CLEAN

build-extbuilder-$1:
	docker build \
		extbuilder/ \
		-f extbuilder/Dockerfile \
		--build-arg=PG_VERSION=$1 \
		--build-arg=PG_MAJOR=$2 \
		--build-arg=PG19_SOURCE_REF=${PG19_SOURCE_REF} \
		--tag=${DOCKER_REPO}/extbuilder:$3${TAG_SUFFIX}

build-all:: build-extbuilder-$1

build-extbuilder-all:: build-extbuilder-$1

push-extbuilder-$1: build-extbuilder-$1
	docker push ${DOCKER_REPO}/extbuilder:$3${TAG_SUFFIX}

push-all:: push-extbuilder-$1

push-extbuilder-all:: push-extbuilder-$1

build-exttester-$1:
	docker build . \
		-f exttester/Dockerfile \
		--build-arg=PG_VERSION=$1 \
		--build-arg=PG_MAJOR=$2 \
		--build-arg=PG_VERSION_CLEAN=$3 \
		--build-arg=PG19_SOURCE_REF=${PG19_SOURCE_REF} \
		--build-arg=CITUS_VERSION="$(call get_last_citus_version,$2)" \
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
		--build-arg=PG19_SOURCE_REF=${PG19_SOURCE_REF} \
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

define make-citus-upgrade-targets
# $1 = PG_VERSION
# $2 = PG_MAJOR
# $3 = PG_VERSION_CLEAN

build-citusupgradetester-$1:
	docker build \
		citusupgradetester/ \
		-f citusupgradetester/Dockerfile \
		--build-arg=PG_VERSION=$1 \
		--build-arg=PG_MAJOR=$2 \
		--build-arg=PG19_SOURCE_REF=${PG19_SOURCE_REF} \
		--build-arg=CITUS_VERSIONS="$(call get_citus_versions,$2)" \
		--tag=${DOCKER_REPO}/citusupgradetester:$3${TAG_SUFFIX}

build-all:: build-citusupgradetester-$1
build-citusupgradetester-all:: build-citusupgradetester-$1

push-citusupgradetester-$1: build-citusupgradetester-$1
	docker push ${DOCKER_REPO}/citusupgradetester:$3${TAG_SUFFIX}

push-all:: push-citusupgradetester-$1
push-citusupgradetester-all:: push-citusupgradetester-$1
endef
$(foreach element,$(CITUS_UPGRADE_PG_VERSIONS),$(eval $(call make-citus-upgrade-targets,$(element),$(shell echo $(element) | awk -F'[^0-9]*' '/[0-9]/ { print $$1 }'),$(shell echo $(element) | sed 's/~//'))))


# pg upgrade image is 1 global image
build-pgupgradetester:
	docker build \
		pgupgradetester/ \
		-f pgupgradetester/Dockerfile \
		--build-arg=PG_VERSIONS="${PG_VERSIONS}" \
		--build-arg=PG19_SOURCE_REF=${PG19_SOURCE_REF} \
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
