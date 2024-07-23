# postgres doesn't ship their isolation tester in the server-dev images
# we use this builder to build the isolation tester from a specific version
FROM buildpack-deps:bullseye AS dev-tools-builder

RUN <<'EOF'
# install dependencies
set -eux

apt-get update

apt-get install -y --no-install-recommends \
    apt-transport-https \
    autoconf \
    build-essential \
    ca-certificates \
    curl \
    debian-archive-keyring \
    gcc \
    gnupg \
    gosu \
    libcurl4 \
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
    bison \
    flex \

# clear apt cache
rm -rf /var/lib/apt/lists/*
EOF

ARG PG_VERSION
ARG PG_VERSION_CLEAN
ARG PG_MAJOR

WORKDIR /build/
RUN curl -fLO "http://ftp.postgresql.org/pub/source/v${PG_VERSION_CLEAN}/postgresql-${PG_VERSION_CLEAN}.tar.bz2"

RUN tar jxf "postgresql-${PG_VERSION_CLEAN}.tar.bz2"

# apply optional patches that might be required for a successful testsuite
WORKDIR /build/postgresql-${PG_VERSION_CLEAN}/
COPY patches/ patches/
RUN <<'EOF'
# apply postgres patches

set -eux
if [ -d "patches/${PG_VERSION_CLEAN}/" ];
then
    git apply patches/${PG_VERSION_CLEAN}/*.patch;
fi;
EOF

WORKDIR /build/postgresql-${PG_VERSION_CLEAN}/build
RUN ../configure --prefix /usr/lib/postgresql/${PG_MAJOR}/
RUN make -sj8

FROM buildpack-deps:bullseye AS dev-tools-collection

WORKDIR /collect

# TODO prepare all these copies in an intermediate layer
ARG PG_VERSION
ARG PG_VERSION_CLEAN
ARG PG_MAJOR

COPY --from=dev-tools-builder \
  /build/postgresql-${PG_VERSION_CLEAN}/build/src/test/isolation/pg_isolation_regress \
  /build/postgresql-${PG_VERSION_CLEAN}/build/src/test/isolation/isolationtester \
  build/postgresql-${PG_MAJOR}/build/src/test/isolation/

# copy regress files in multiple layers as we only need a few
COPY --from=dev-tools-builder /build/postgresql-${PG_VERSION_CLEAN}/build/src/test/regress/regress.so usr/lib/postgresql/${PG_MAJOR}/lib/
COPY --from=dev-tools-builder /build/postgresql-${PG_VERSION_CLEAN}/src/test/regress/ usr/lib/postgresql/${PG_MAJOR}/lib/regress/
RUN rm -rf usr/lib/postgresql/${PG_MAJOR}/lib/regress/*.c usr/lib/postgresql/${PG_MAJOR}/lib/regress/*.h

FROM buildpack-deps:bullseye

# add unpriviliged user for tests
RUN useradd -ms /bin/bash circleci

RUN <<'EOF'
# install dependencies
set -eux

apt-get update

apt-get install -y --no-install-recommends \
    apt-transport-https \
    autoconf \
    build-essential \
    ca-certificates \
    cpanminus \
    curl \
    debian-archive-keyring \
    gcc \
    gdb \
    gnupg \
    gosu \
    lcov \
    libcurl4 \
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
    bison \
    flex \

# clear apt cache
rm -rf /var/lib/apt/lists/*
EOF

# install rust
RUN curl --proto '=https' --tlsv1.2 --silent --show-error https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

# perl's lib IPC::Run is required to run tap tests
RUN cpanm install IPC::Run

# make special locales available
COPY locale.gen /etc/locale.gen
RUN locale-gen

# Add codeclimate
RUN curl -L https://codeclimate.com/downloads/test-reporter/test-reporter-latest-linux-amd64 > /usr/local/bin/cc-test-reporter && chmod +x /usr/local/bin/cc-test-reporter

ARG PG_VERSION
ARG PG_MAJOR
ENV PG_VERSION=$PG_VERSION
ENV PG_MAJOR=$PG_MAJOR

RUN <<'EOF'
# install postgres ecosystem for pg version: $PG_VERSION
set -eux

# install key and repositories
curl -sf https://www.postgresql.org/media/keys/ACCC4CF8.asc | APT_KEY_DONT_WARN_ON_DANGEROUS_USAGE=1 apt-key add -
echo "deb https://apt.postgresql.org/pub/repos/apt bullseye-pgdg main" >> /etc/apt/sources.list.d/postgresql.list
echo "deb https://apt-archive.postgresql.org/pub/repos/apt bullseye-pgdg-archive main" >> /etc/apt/sources.list.d/postgresql.list

apt-get update

# infer the pgdgversion of postgres based on the $PG_VERSION
pgdg_version=$(apt list -a postgresql-server-dev-${PG_MAJOR} 2>/dev/null | grep "${PG_VERSION}" | awk '{print $2}' | head -n1 )

apt-get install -y --no-install-recommends --allow-downgrades \
    libdbi-perl \
    libdbd-pg-perl \
    libpq-dev=${pgdg_version} \
    libpq5=${pgdg_version} \
    postgresql-${PG_MAJOR}=${pgdg_version} \
    postgresql-client-${PG_MAJOR}=${pgdg_version} \
    postgresql-${PG_MAJOR}-dbgsym=${pgdg_version} \
    postgresql-server-dev-${PG_MAJOR}=${pgdg_version} \

# wal2json not available yet for PG17
if [ "$PG_MAJOR" != "17" ];
then
    apt-get install -y --no-install-recommends --allow-downgrades postgresql-${PG_MAJOR}-wal2json;
fi;

    # clear apt cache
rm -rf /var/lib/apt/lists/*
EOF

# add postgress to the path
ENV PATH=/usr/lib/postgresql/$PG_MAJOR/bin/:$PATH

# setup /var/run/postgresql for use with circleci
RUN mkdir -p /var/run/postgresql && chown -R postgres:postgres /var/run/postgresql && chmod 2777 /var/run/postgresql

# copy the collected files from the collection container at once into the final container
COPY --from=dev-tools-collection /collect/ /

WORKDIR /home/circleci
