FROM python:3.6-slim-stretch AS base

# add unpriviliged user for tests
RUN useradd -ms /bin/bash circleci

RUN apt-get update \
# install dependencies
 && apt-get install -y --no-install-recommends \
    apt-transport-https \
    autoconf \
    build-essential \
    ca-certificates \
    curl \
    debian-archive-keyring \
    gnupg \
    gosu \
    libcurl3 \
    libcurl4-openssl-dev \
    libicu-dev \
    libreadline-dev \
    libselinux1-dev \
    libssl-dev \
    libxslt-dev \
    locales \
    make \
    perl \
# clear apt cache
 && rm -rf /var/lib/apt/lists/*

# make special locales available
COPY locale.gen /etc/locale.gen
RUN locale-gen

# add postgres signing key
RUN curl -sf https://www.postgresql.org/media/keys/ACCC4CF8.asc | APT_KEY_DONT_WARN_ON_DANGEROUS_USAGE=1 apt-key add -

ARG PG_VERSION
ARG PG_MAJOR
ENV PG_VERSION=$PG_VERSION
ENV PG_MAJOR=$PG_MAJOR

# add postgres repository
RUN echo "deb https://apt-archive.postgresql.org/pub/repos/apt stretch-pgdg-archive main" > /etc/apt/sources.list.d/postgresql.list \
 && apt-get update \
# infer the pgdgversion of postgres based on the $PG_VERSION
 && pgdg_version=$(apt list -a postgresql-server-dev-${PG_MAJOR} 2>/dev/null | grep "${PG_VERSION}" | awk '{print $2}') \
 && apt-get install -y --no-install-recommends \
    postgresql-client-${PG_MAJOR}=${pgdg_version} \
    postgresql-${PG_MAJOR}=${pgdg_version} \
    postgresql-server-dev-${PG_MAJOR}=${pgdg_version} \
# clear apt cache
 && rm -rf /var/lib/apt/lists/*

# add postgress to the path
ENV PATH=/usr/lib/postgresql/$PG_MAJOR/bin/:$PATH

# setup /var/run/postgresql for use with circleci
RUN mkdir -p /var/run/postgresql && chown -R postgres:postgres /var/run/postgresql && chmod 2777 /var/run/postgresql

##############################################################################
FROM base AS builder

RUN apt update \
 && apt install -y \
    git \
    libkrb5-dev \
 && rm -rf /var/lib/apt/lists/*

ARG CITUS_VERSIONS
ENV CITUS_VERSIONS=$CITUS_VERSIONS

WORKDIR /build/

COPY files/sbin/build-citus .
RUN ./build-citus

##############################################################################
FROM base

# we need to be able to untar the binaries as the circleci user
RUN chown -R circleci /usr/lib/postgresql/ /usr/include/postgresql/ /usr/share/postgresql/

COPY ./files/etc/requirements.txt /tmp/etc/
RUN pip3 install -Ir /tmp/etc/requirements.txt

WORKDIR /home/circleci

ARG CITUS_VERSIONS
ENV CITUS_VERSIONS=$CITUS_VERSIONS

# copy compiled citus versions
COPY --from=builder /build/ /
