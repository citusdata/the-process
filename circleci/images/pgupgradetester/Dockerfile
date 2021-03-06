FROM python:3.6-slim-stretch

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
    liblz4-1 \
    liblz4-dev \
    libreadline-dev \
    libselinux1-dev \
    libssl-dev \
    libxslt-dev \
    libzstd-dev \
    libzstd1 \
    make \
    perl \
# clear apt cache
 && rm -rf /var/lib/apt/lists/*

 # add postgres signing key
RUN curl -sf https://www.postgresql.org/media/keys/ACCC4CF8.asc | APT_KEY_DONT_WARN_ON_DANGEROUS_USAGE=1 apt-key add -

ARG PG_VERSIONS
ENV PG_VERSIONS=$PG_VERSIONS

# Hacky way to fetch all the pgdg versions so we can pin them
# you will find the sequence '"'"' a couple of times. This is to
# insert a ' character into the -c argument to bash.
# The reason for this convoluted way of installing postgres is
# because docker uses /bin/sh to execute the RUN commands where
# the below code requires /bin/bash.
SHELL ["/bin/bash", "-c"]
RUN echo "deb https://apt-archive.postgresql.org/pub/repos/apt stretch-pgdg-archive main" > /etc/apt/sources.list.d/postgresql.list \
 && apt-get update \
 && pkgs=(); \
    for PG_VERSION in $PG_VERSIONS; do \
        PG_MAJOR=$(echo ${PG_VERSION} | awk -F'[^0-9]*' '/[0-9]/ { print $1 }'); \
        pgdg_version=$(apt list -a postgresql-server-dev-${PG_MAJOR} 2>/dev/null | grep "${PG_VERSION}" | awk '{print $2}'); \
        pkgs+=("postgresql-client-${PG_MAJOR}=${pgdg_version}"); \
        pkgs+=("postgresql-${PG_MAJOR}=${pgdg_version}"); \
        pkgs+=("postgresql-server-dev-${PG_MAJOR}=${pgdg_version}"); \
    done; \
    echo ${pkgs[@]}\
 && apt-get install -y --no-install-recommends \
    postgresql-common \
    ${pkgs[@]} \
 && rm -rf /var/lib/apt/lists/*

# setup /var/run/postgresql for use with circleci
RUN mkdir -p /var/run/postgresql && chown -R postgres:postgres /var/run/postgresql && chmod 2777 /var/run/postgresql

COPY ./files/etc/requirements.txt /tmp/etc/
RUN pip3 install -Ir /tmp/etc/requirements.txt
