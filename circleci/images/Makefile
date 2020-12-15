# config variable
DOCKER_REPO=citus

# runtime variables
PG_VERSION := 13.1

# auto generated variables
PG_MAJOR := $(shell echo $(PG_VERSION) | awk -F'[^0-9]*' '/[0-9]/ { print $$1 }')
TAG_SUFFIX := '-dev' # todo, add unique thing, empty for release version

images: build-exttester

build-exttester:
	docker build \
		exttester/ \
		-f exttester/Dockerfile \
		--build-arg=PG_VERSION=${PG_VERSION} \
		--build-arg=PG_MAJOR=${PG_MAJOR} \
		--tag=${DOCKER_REPO}/exttester:${PG_VERSION}${TAG_SUFFIX}
