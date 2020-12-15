# config variable
DOCKER_REPO=citus

# auto generated variables
TAG_SUFFIX := -dev$(shell date +'%Y%m%d%H%M')# todo, add unique thing, empty for release version

# code below creates targets for all postgres verions in PG_VERSIONS
PG_VERSIONS = 11.10 12.5 13.1
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

# upgrade image is 1 global image
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
