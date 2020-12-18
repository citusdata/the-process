# Table of Contents

* [Introduction](#Introduction)
* [1. Makefile](#1-makefile)
* [2. Images](#2-images)
  * [extbuilder](#extbuilder)
  * [exttester](#exttester)
  * [failtester](#failtester)
  * [pgupgradetester](#pgupgradetester)
  * [citusupgradetester](#citusupgradetester)
  * [stylechecker](#stylechecker)

## Introduction

This repository contains the source code for docker images that are used in [citus testing](https://github.com/citusdata/citus/blob/master/.circleci/config.yml). The images are pushed to [docker hub](https://hub.docker.com/u/citus). There is no hooking logic between this repository and the docker hub account. It is used purely for the storage of our images source code.

## 1. Makefile

The creation of the images is driven by the [Makefile](circleci/images/Makefile). The Makefile has the list of pinned versions of postgres we build against. For images specific to the postgres version there will be targets to build and push the image for a specific postgres version, or all pinned versions at once. Secondly all images can be build with the `build-all` target and pushed with `push-all`.

During development and maintenance of the images you can freely call `make` with the desired targets. The images will be tagged with a `-devYYYYmmddHHMM` suffix to indicate these are development images. Since the minute is included in the tag, most often this will create new tags for every run. A new tag doesn't mean new images. The normal docker caching system is active. When a layer does not change it will be reused in a new tagged artifact.

When ready to release run `make` with the `REALESE` veriable set to `1`.

    $ RELEASE=1 make push-all

This will push all images, building all layers that might have changed since the last run of build. Make sure you have tested the images before pushing a release. CI might start using the newly pushed images directly, depending on the availability of a cache and how it is invalidated.

Before being able to push to the docker registry you need to have your cli authenticated to the docker hub and have sufficient privileges to push to the registery.

If you don't have access, or want to push the images to a private repo, the repo can be changed at runtime with the `DOCKER_REPO` variable like:

    $ DOCKER_REPO=private-repo make push-all

## 2. Images

Details on the images. Mostly uninteresting for users. Please refer to the [Makefile](#1-makefile) section above.

### extbuilder

The [extbuilder](https://github.com/citusdata/the-process/tree/master/circleci/images/extbuilder) image is the first image that other jobs depend on in our tests. The [extbuilder](https://github.com/citusdata/the-process/tree/master/circleci/images/extbuilder):

This image contains all the artifacts required to produce a build of citus binaries for exactly 1 postgres version. This image is build for every supported Postgres version. Any scripts driving the build are contained in the citus repostiroy.

The postgres version is installed from the pgdg apt archive. This allows us to install older versions, and therefore keep the versions of postgres pinned during normal release cycles. To bump the version of the Postgres to build against one should change the version as pinned in the `Makefile`

### exttester

Very comparable to the `extbuilder` (todo: merge the images together - yes they are that similar). This image however is slightly optimized for actually running the tests of citus against 1 postgres version.

### failtester

This image is functionally a specialization of the [exttester](#exttester) image. It has extra tools for running the failure tests of Citus. Due to how the image is structured there is very little in common. This image starts from a python based and add the postgres versions on top. Finally it includes all the python libraries

### pgupgradetester

This image is also a specialization of the [exttester](#exttester) on a functional level, and has many overlaps with [failtester](#failtester), so much so that I also feel we can merge these together at some point in the future.

### citusupgradetester

This container is a special beast. Besides having the testing dependencies installed like [pgupgradetester](#pgupgradetester) and [failtester](#failtester), it also contains the binaries of older citus versions. During the testrun they can actually be installed at will by the testing harness to simulate a citus upgrade.

### stylechecker

TODO: this image has not changed and is currently not build by the Makefile. Future work.