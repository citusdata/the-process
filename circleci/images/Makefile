# config variable
DOCKER_REPO ?= ghcr.io/citusdata
SHA_SUFFIX := $(shell git rev-parse --short HEAD)

# auto generated variables
ifdef RELEASE
	TAG_SUFFIX := -v${SHA_SUFFIX}
else
	TAG_SUFFIX := -dev-${SHA_SUFFIX}
endif

# all postgres versions we test against
PG_VERSIONS=$(shell cat PG_VERSIONS|cut -c 6-|tr '\n' ' ' )

PG_UPGRADE_TESTER_VERSION=$(shell echo ${PG_VERSIONS}|tr ' ' '-'|sed 's/~//g')

STYLE_CHECKER_TOOLS_VERSION=0.8.18

# we should add more majors/citus versions when we address https://github.com/citusdata/citus/issues/4807
CITUS_UPGRADE_PG_VERSIONS=$(shell head -n1 PG_VERSIONS|cut -c 6-|tr '\n' ' ' )
# 10.2.0 is the oldest version supporting PG14, whereas 11.3.0 is for upgrade_pg_dist_cleanup tests
CITUS_UPGRADE_VERSIONS=v10.2.0 v11.3.0

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
		--build-arg=CITUS_VERSIONS="${CITUS_UPGRADE_VERSIONS}"\
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
