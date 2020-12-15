FROM python:3.6-slim-stretch

# add unpriviliged user for tests
RUN useradd -ms /bin/bash circleci

RUN apt-get update \
# install dependencies
 && apt-get install -y --no-install-recommends \
    apt-transport-https \
    ca-certificates \
    curl \
    debian-archive-keyring \
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

# make special locales available
COPY locale.gen /etc/locale.gen
RUN locale-gen

COPY ./files/etc/requirements.txt /tmp/etc/
RUN pip3 install -Ir /tmp/etc/requirements.txt

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

WORKDIR /home/circleci
