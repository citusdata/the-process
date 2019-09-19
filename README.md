# The Process

This repository contains the source code for docker images that are used in [citus testing](https://github.com/citusdata/citus/blob/master/.circleci/config.yml).  

The [extbuilder](https://github.com/citusdata/the-process/tree/master/circleci/images/extbuilder) image is the core image that other jobs depend on in our tests. The [extbuilder](https://github.com/citusdata/the-process/tree/master/circleci/images/extbuilder):

- Installs postgres 10 and 11 `pg_config`. We only need `pg_config` to generate citus artifacts.
- Installs and tars the checked out citus version for the postgres versions. This is done so that the other jobs can install citus easily without the need to do `make install`.
- Creates `build-{pg_version}` folders with citus configured, so these folders have the necessary `Makefile.global` to run the tests. These folders are generated for each postgres version. For example, at the time of writing there are 2 folders with `build-10` and `build-11`.

The general process for other images are similar, which is:

- Untar the citus tar to install citus for the postgres version that the image will use. For example, if postgres 11 is used, the tar is named `install-11.tar`.
- The script (`install-and-test-ext`) takes the target name as an argument, and the following command is used to run the test:

```bash
gosu circleci make -C "${CIRCLE_WORKING_DIRECTORY}/build-${PG_MAJOR}/src/test/regress" "${@}"
```

- Finally `regression.diffs` is printed if it exists, which indicates that there was a problem during the tests.

## How to publish a change

If you want to make a change and push it to docker hub, you should do:

- Clone the repository and make the necessary changes
- Build the image

```bash
docker build --tag={repositoryName}/{imageName} .
```

- Login to your account

```bash
docker login # enter your crendentials
```

- Push the image

```bash
docker push {repositoryName}/{imageName}
```
