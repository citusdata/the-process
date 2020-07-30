# Table of Contents

* [Introduction](#Introduction)
* [1. Images](#1-images)
  * [1.1 How circleci uses our images in testing](#11-How-circleci-uses-our-images-in-testing)
* [2. How to update images](#2-How-to-update-images)
  * [2.1 How to update a postgres minor version in images](#2.1-How-to-update-postgres-minor-version-in-images)
  * [2.2 How to add a major postgres major](#2.2-How-to-add-a-major-postgres-major)
* [3. How to publish a change](#3-How-to-publish-a-change)

## Introduction

This repository contains the source code for docker images that are used in [citus testing](https://github.com/citusdata/citus/blob/master/.circleci/config.yml). The images are pushed to [docker hub](https://hub.docker.com/u/citus). There is no hooking logic between this repository and the docker hub account. It is used purely for the storage of our images source code.

## 1. Images

The [extbuilder](https://github.com/citusdata/the-process/tree/master/circleci/images/extbuilder) image is the core image that other jobs depend on in our tests. The [extbuilder](https://github.com/citusdata/the-process/tree/master/circleci/images/extbuilder):

While building the image:

* Installs postgres majors' `pg_config`. We only need `pg_config` to generate citus artifacts.

While running the container:

* Installs and tars the checked out citus version for the postgres versions. This is done so that the other jobs can install citus easily by untarring without the need to do `make install`. We need to do this step in the running container, not while building the image, so that the built citus version is the checked out citus code.
* Creates `build-{pg_version}` folders with citus configured, so these folders have the necessary `Makefile.global` to run the tests. These folders are generated for each postgres version. For example, at the time of writing there are 3 folders with `build-10`, `build-11` and `build-12`.

The general process for other images are similar, which is:

While building the image:

* Install postgres major which is taken as an argument `PG_MAJOR`.

While running the container:

* Untar the citus tar to install citus for the postgres version that the image will use. For example, if postgres 11 is used, the tar is named `install-11.tar`.
* The script (`install-and-test-ext`) takes the target name as an argument, and the following command is used to run the test:

```bash
gosu circleci make -C "${CIRCLE_WORKING_DIRECTORY}/build-${PG_MAJOR}/src/test/regress" "${@}"
```

* Finally `regression.diffs` is printed if it exists, which indicates that there was a problem during the tests.

Because of the specific logic that we have to run tests faster, we have a docker image `debbuilder` that generates a debian package for `postgresql-server-dev-{pg-major}`. The generated package is in the built docker image, specifically in `{container-name}/home/circleci/debs`. The package is pushed to [the-process](https://packagecloud.io/citus-bot/the-process). This package place is added to apt source list and pinned with with the highest priority so that it is chosen over the standard `postgresql-server-dev-{pg-major}` package.

The installation of postgres packages is at the time of building the image to reduce testing time. However this means that once the image is built the postgres version is fixed. You will need to rebuild the image if you want to upgrade the image, upgrading the image for a minor version is easier compared to upgrading a major version.

### 1.1. How circleci uses our images in testing

Our [dockerhub account](https://hub.docker.com/u/citus) has all the images here except the `debbuilder`. When a change is committed, circleci:

* Pulls the `https://hub.docker.com/r/citus/extbuilder` image, generates the citus artifacts which other images will use for testing.
* All of our test jobs wait for `extbuilder` to be completed. Once that is done, all of the jobs are run in parallel without any specific order(It is possible that some jobs are waiting because of parallelism limit in our circleci).
* All the test jobs use the artifacts that are generated with `extbuilder`.

Refer to [images](#1-images) for more details.

## 2. How to update images

While updating images, if the image uses python such as `failtester`, you will need to update the `requirements.txt` as well. We are using `pipenv` for development in [citus](https://github.com/citusdata/citus) but we generate `requirements.txt` file with `pipenv` to install our python dependencies. Running something like the following should generate `requirements.txt`:

```bash
 pipenv lock --requirements > requirements.txt
```

Make sure that you include the commit id of citus at the beginning of the generated `requirements.txt`. If you are adding a new python dependency you will need to repeat this process for images to be updated and have the correct dependencies.

### 2.1 How to update postgres minor version in images

To update a postgres minor version, you will need to generate a `debian` package:

* Generate `postgresql-server-dev-{pg-major}` package with `debbuilder` image.
* The generated package will be in `{container-name}/home/circleci/debs`. One way of getting the package from the docker image is:
  * Run the container with `docker run -it {tag-name} bash`
  * Find the name of your container with `docker ps`
  * Copy the `debs` folder from docker container to your local `docker cp {container-name}:/home/circleci/debs .`
* Upload the package to [the-process](https://packagecloud.io/citus-bot/the-process). Make sure that you choose `debian stretch` while uploading. In order to upload you can:
  * Upload the package file from the UI by clicking to `Upload image`
  * Or you can use the [package cloud cli](https://packagecloud.io/l/cli).

After adding the package to `package cloud`:

And for all images follow the instructions on [how to publish a change](#4-How-to-publish-a-change)

### 2.2. How to add a postgres major

If you want to add support for a major postgres major, like `pg-13` you will need to do the steps that are not limited to:

* Generate `postgresql-server-dev-{pg-major}` package with `debbuilder` image. Make sure to add the package index for `pg-major` in `/etc/apt/sources.list.d/pgdg.list`(See [this](https://apt.postgresql.org/pub/repos/apt/dists/)).You can see find the related part [here](https://github.com/citusdata/the-process/blob/master/circleci/images/debbuilder/files/install-builddeps). Basically replace the last one with the new postgres version such as `12` -> `13`.

```bash
cd debbuilder
docker build --tag=citus/debbuilder13 . --build-arg PG_MAJORS=13
```

* The generated package will be in `{container-name}/home/circleci/debs`. One way of getting the package from the docker image is:
  * Run the container with `docker run -it {tag-name} bash`
  * Find the name of your container with `docker ps`
  * Copy the `debs` folder from docker container to your local `docker cp {container-name}:/home/circleci/debs .`
* Upload the package to [the-process](https://packagecloud.io/citus-bot/the-process). Make sure that you choose `debian stretch` while uploading. Use `citus-bot` account there(learn the credentials from someone). In order to upload you can:
  * Upload the package file from the UI by clicking to `Upload image`
  * Or you can use the [package cloud cli](https://packagecloud.io/l/cli).
  
* Add `pg-major` to `extbuilder` in its script so that citus artifacts are generated for that `pg_major` too.
* Update `pg_latest`.
* (This step should already be done if you update `pg_latest`). Add new `pg-major` package index to `sources.list`:

```bash
# add pgdg repo to sources
echo "Writing /etc/apt/sources.list.d/pgdg.list..." >&2
echo "deb http://apt.postgresql.org/pub/repos/apt/ ${codename}-pgdg main ${PG-MAJOR}" > \
    /etc/apt/sources.list.d/postgresql.list
```

```bash
cd extbuilder
docker build --tag=citus/extbuilder-{pg-major} .
```

* Build `exttester` with `pg-major`:

```bash
cd exttester
docker build --tag=citus/exttester-{pg-major} . --build-arg PG_MAJOR={pg-major}
```

* Build `failtester` with `pg-major`:

```bash
cd failtester
docker build --tag=citus/failtester-{pg-major} . --build-arg PG_MAJOR={pg-major}
```

## 3. How to publish a change

If you want to make a change and push it to docker hub, you should do:

* Clone the repository and make the necessary changes
* Build the image

```bash
docker build --tag={repositoryName}/{imageName} .
```

* Login to your account

```bash
docker login # enter your crendentials
```

* Push the image

```bash
docker push {repositoryName}/{imageName}
```
