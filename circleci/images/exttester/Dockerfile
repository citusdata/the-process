# postgres doesn't ship their isolation tester in the server-dev images
# we use this builder to build the isolation tester from a specific version
FROM buildpack-deps:stretch AS dev-tools-builder

RUN apt-get update \
# install dependencies
 && apt-get install -y --no-install-recommends \
    apt-transport-https \
    autoconf \
    build-essential \
    ca-certificates \
    curl \
    debian-archive-keyring \
    gcc \
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
    locales \
    make \
    perl \
# clear apt cache
 && rm -rf /var/lib/apt/lists/*

ARG PG_VERSION
ARG PG_MAJOR

WORKDIR /build/
RUN curl -fLO "http://ftp.postgresql.org/pub/source/v${PG_VERSION}/postgresql-${PG_VERSION}.tar.bz2"

RUN tar jxf "postgresql-${PG_VERSION}.tar.bz2"

# apply optional patches that might be required for a successful testsuite
WORKDIR /build/postgresql-${PG_VERSION}/
COPY patches/ patches/
SHELL ["/bin/bash", "-c"]
RUN if [ -d "patches/${PG_VERSION}/" ]; \
    then \
        git apply patches/${PG_VERSION}/*.patch; \
    fi;

WORKDIR /build/postgresql-${PG_VERSION}/build
RUN ../configure --prefix /usr/lib/postgresql/${PG_MAJOR}/
RUN make -sj8

FROM buildpack-deps:stretch AS dev-tools-collection

WORKDIR /collect

# TODO prepare all these copies in an intermediate layer
ARG PG_VERSION
ARG PG_MAJOR

COPY --from=dev-tools-builder \
	/build/postgresql-${PG_VERSION}/build/src/test/isolation/pg_isolation_regress \
	/build/postgresql-${PG_VERSION}/build/src/test/isolation/isolationtester \
	build/postgresql-${PG_MAJOR}/build/src/test/isolation/

# copy regress files in multiple layers as we only need a few
COPY --from=dev-tools-builder /build/postgresql-${PG_VERSION}/build/src/test/regress/regress.so usr/lib/postgresql/${PG_MAJOR}/lib/
COPY --from=dev-tools-builder /build/postgresql-${PG_VERSION}/src/test/regress/ usr/lib/postgresql/${PG_MAJOR}/lib/regress/
RUN rm -rf usr/lib/postgresql/${PG_MAJOR}/lib/regress/*.c usr/lib/postgresql/${PG_MAJOR}/lib/regress/*.h

FROM buildpack-deps:stretch

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
    gcc \
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

# copy the collected files from the collection container at once into the final container
COPY --from=dev-tools-collection /collect/ /

WORKDIR /home/circleci
