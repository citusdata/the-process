# postgres doesn't ship their isolation tester in the server-dev images
# we use this builder to build the isolation tester from a specific version
FROM buildpack-deps:stretch AS dev-tools-builder

RUN apt-get update \
# install dependencies
 && apt-get install -y --no-install-recommends \
    apt-transport-https \
    ca-certificates \
    curl \
    debian-archive-keyring \
    gcc \
    gnupg \
    gosu \
    make \
    perl \
    autoconf \
    build-essential \
    libcurl3 \
    libcurl4-openssl-dev \
    libicu-dev \
    libreadline-dev \
    libselinux1-dev \
    libxslt-dev \
    libssl-dev \
    locales \
# clear apt cache
 && rm -rf /var/lib/apt/lists/*

ARG PG_VERSION
ARG PG_MAJOR

WORKDIR /build/
RUN curl -fLO "http://ftp.postgresql.org/pub/source/v${PG_VERSION}/postgresql-${PG_VERSION}.tar.bz2"

RUN tar jxf "postgresql-${PG_VERSION}.tar.bz2"
WORKDIR /build/postgresql-${PG_VERSION}/build
RUN ../configure --prefix /usr/lib/postgresql/${PG_MAJOR}/
RUN make -sj8

RUN ls /build/postgresql-${PG_VERSION}/build/
RUN ls /build/postgresql-${PG_VERSION}/build/src/
RUN ls /build/postgresql-${PG_VERSION}/build/src/test/

# TODO read the PG_MAJOR from PG_VERSION and install that actual version
FROM buildpack-deps:stretch

RUN apt-get update \
# install dependencies
 && apt-get install -y --no-install-recommends \
    apt-transport-https \
    ca-certificates \
    curl \
    debian-archive-keyring \
    gcc \
    gnupg \
    gosu \
    make \
    perl \
    autoconf \
    build-essential \
    libcurl3 \
    libcurl4-openssl-dev \
    libicu-dev \
    libreadline-dev \
    libselinux1-dev \
    libxslt-dev \
    libssl-dev \
    locales \
# clear apt cache
 && rm -rf /var/lib/apt/lists/*

# add unpriviliged user for tests
RUN useradd -ms /bin/bash circleci

# make special locales available
COPY locale.gen /etc/locale.gen
RUN locale-gen

# add postgres signing key
RUN curl -sf https://www.postgresql.org/media/keys/ACCC4CF8.asc | APT_KEY_DONT_WARN_ON_DANGEROUS_USAGE=1 apt-key add -

ARG PG_MAJOR
ENV PG_MAJOR=$PG_MAJOR

# add postgres repository
RUN echo "deb http://apt.postgresql.org/pub/repos/apt/ stretch-pgdg main ${PG_MAJOR}" > /etc/apt/sources.list.d/postgresql.list
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    postgresql-common \
    postgresql-${PG_MAJOR} \
    postgresql-server-dev-${PG_MAJOR} \
# clear apt cache
 && rm -rf /var/lib/apt/lists/*

# add postgress to the path
ENV PATH=/usr/lib/postgresql/$PG_MAJOR/bin/:$PATH

# setup /var/run/postgresql for use with circleci
RUN mkdir -p /var/run/postgresql && chown -R postgres:postgres /var/run/postgresql && chmod 2777 /var/run/postgresql

# TODO prepare all these copies in an intermediate layer
ARG PG_VERSION
COPY --from=dev-tools-builder /build/postgresql-${PG_VERSION}/build/src/test/isolation/pg_isolation_regress /build/postgresql-${PG_VERSION}/build/src/test/isolation/isolationtester /build/postgresql-${PG_MAJOR}/build/src/test/isolation/
# COPY --from=dev-tools-builder /build/postgresql-${PG_VERSION}/build/src/test/regress/pg_regress /build/postgresql-${PG_MAJOR}/build/src/test/regress/pg_regress

# copy regress files in multiple layers as we only need a few
COPY --from=dev-tools-builder /build/postgresql-${PG_VERSION}/src/test/regress/data/ /usr/lib/postgresql/13/lib/regress/data/
COPY --from=dev-tools-builder /build/postgresql-${PG_VERSION}/src/test/regress/expected/ /usr/lib/postgresql/13/lib/regress/expected/
COPY --from=dev-tools-builder /build/postgresql-${PG_VERSION}/src/test/regress/input/ /usr/lib/postgresql/13/lib/regress/input/
COPY --from=dev-tools-builder /build/postgresql-${PG_VERSION}/src/test/regress/output/ /usr/lib/postgresql/13/lib/regress/output/
COPY --from=dev-tools-builder /build/postgresql-${PG_VERSION}/src/test/regress/sql/ /usr/lib/postgresql/13/lib/regress/sql/

COPY --from=dev-tools-builder \
	/build/postgresql-${PG_VERSION}/src/test/regress/Makefile \
	/build/postgresql-${PG_VERSION}/src/test/regress/parallel_schedule \
	/build/postgresql-${PG_VERSION}/src/test/regress/resultmap \
	/build/postgresql-${PG_VERSION}/src/test/regress/serial_schedule \
	/usr/lib/postgresql/13/lib/regress/

COPY --from=dev-tools-builder \
	/build/postgresql-${PG_VERSION}/build/src/test/regress/regress.so \
	/usr/lib/postgresql/${PG_MAJOR}/lib/regress.so

WORKDIR /home/circleci
