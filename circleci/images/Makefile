# config variable
DOCKER_REPO ?= citus

# auto generated variables
ifdef RELEASE
	TAG_SUFFIX :=
else
	TAG_SUFFIX := -dev$(shell date +'%Y%m%d%H%M')
endif

# all postgres versions we test against
PG_VERSIONS = 11.9 12.4 13.0

# citus version 8.x only supports 11, when bumping versions below we can create more images
CITUS_UPGRADE_PG_VERSIONS = 11.9
CITUS_UPGRADE_VERSIONS = v8.0.0 v8.1.0 v8.2.0 v8.3.0

# code below creates targets for all postgres versions in PG_VERSIONS
define make-image-targets
# $1 = PG_VERSION
# $2 = PG_MAJOR

build-extbuilder-$1:
	docker build \
		extbuilder/ \
		-f extbuilder/Dockerfile \
		--build-arg=PG_VERSION=$1 \
		--build-arg=PG_MAJOR=$2 \
		--tag=${DOCKER_REPO}/extbuilder:$1${TAG_SUFFIX}

build-all:: build-extbuilder-$1

build-extbuilder-all:: build-extbuilder-$1

push-extbuilder-$1: build-extbuilder-$1
	docker push ${DOCKER_REPO}/extbuilder:$1${TAG_SUFFIX}

push-all:: push-extbuilder-$1

push-extbuilder-all:: push-extbuilder-$1

build-exttester-$1:
	docker build \
		exttester/ \
		-f exttester/Dockerfile \
		--build-arg=PG_VERSION=$1 \
		--build-arg=PG_MAJOR=$2 \
		--tag=${DOCKER_REPO}/exttester:$1${TAG_SUFFIX}

build-all:: build-exttester-$1

build-exttester-all:: build-exttester-$1

push-exttester-$1: build-exttester-$1
	docker push ${DOCKER_REPO}/exttester:$1${TAG_SUFFIX}

push-all:: push-exttester-$1

push-exttester-all:: push-exttester-$1

build-failtester-$1:
	docker build \
		failtester/ \
		-f failtester/Dockerfile \
		--build-arg=PG_VERSION=$1 \
		--build-arg=PG_MAJOR=$2 \
		--tag=${DOCKER_REPO}/failtester:$1${TAG_SUFFIX}

build-all:: build-failtester-$1

build-failtester-all:: build-failtester-$1

push-failtester-$1: build-failtester-$1
	docker push ${DOCKER_REPO}/failtester:$1${TAG_SUFFIX}

push-all:: push-failtester-$1

push-failtester-all:: push-failtester-$1
endef

# call make-image-targets($PG_VERSION, $PG_MAJOR) for every version in PG_VERSIONS
$(foreach element,$(PG_VERSIONS),$(eval $(call make-image-targets,$(element),$(shell echo $(element) | awk -F'[^0-9]*' '/[0-9]/ { print $$1 }'))))

define make-citus-upgrage-targets
# $1 = PG_VERSION
# $2 = PG_MAJOR

build-citusupgradetester-$1:
	docker build \
		citusupgradetester/ \
		-f citusupgradetester/Dockerfile \
		--build-arg=PG_VERSION=$1 \
		--build-arg=PG_MAJOR=$2 \
		--build-arg=CITUS_VERSIONS="${CITUS_UPGRADE_VERSIONS}"\
		--tag=${DOCKER_REPO}/citusupgradetester:$1${TAG_SUFFIX}

build-all:: build-citusupgradetester-$1
build-citusupgradetester-all:: build-citusupgradetester-$1

push-citusupgradetester-$1: build-citusupgradetester-$1
	docker push ${DOCKER_REPO}/citusupgradetester:$1${TAG_SUFFIX}

push-all:: push-citusupgradetester-$1
push-citusupgradetester-all:: push-citusupgradetester-$1
endef
$(foreach element,$(CITUS_UPGRADE_PG_VERSIONS),$(eval $(call make-citus-upgrage-targets,$(element),$(shell echo $(element) | awk -F'[^0-9]*' '/[0-9]/ { print $$1 }'))))


# pg upgrade image is 1 global image
build-pgupgradetester:
	docker build \
		pgupgradetester/ \
		-f pgupgradetester/Dockerfile \
		--build-arg=PG_VERSIONS="${PG_VERSIONS}" \
		--tag=${DOCKER_REPO}/pgupgradetester:latest${TAG_SUFFIX}

build-all:: build-pgupgradetester

push-pgupgradetester: build-pgupgradetester
	docker push ${DOCKER_REPO}/pgupgradetester:latest${TAG_SUFFIX}

push-all:: push-pgupgradetester

