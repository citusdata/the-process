FROM buildpack-deps:bookworm

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

# clear apt cache
rm -rf /var/lib/apt/lists/*
EOF

ARG PG_VERSION
ARG PG_MAJOR
ARG PG19_SOURCE_REF
ENV PG_VERSION=$PG_VERSION
ENV PG_MAJOR=$PG_MAJOR
ENV PG19_SOURCE_REF=$PG19_SOURCE_REF

RUN <<'EOF'
# install postgres ecosystem for pg version: $PG_VERSION
set -eux

if [ "${PG_MAJOR}" = "19" ]; then
    # PG19 is unreleased and not on apt.postgresql.org. Build from a pinned
    # upstream source ref so this image can still be produced.
    apt-get update
    apt-get install -y --no-install-recommends \
        bison \
        flex \
        libxml2-dev \
        pkg-config \
        zlib1g-dev

    src_dir=/tmp/pg19-src
    rm -rf "${src_dir}"
    mkdir -p "${src_dir}"
    curl -fsL "https://codeload.github.com/postgres/postgres/tar.gz/${PG19_SOURCE_REF}" \
        | tar -xzf - -C "${src_dir}" --strip-components=1
    cd "${src_dir}"
    ./configure \
        --prefix=/usr/lib/postgresql/${PG_MAJOR} \
        --datarootdir=/usr/share/postgresql/${PG_MAJOR} \
        --includedir=/usr/include/postgresql/${PG_MAJOR} \
        --sysconfdir=/etc/postgresql-common \
        --with-openssl \
        --with-icu \
        --with-libxml \
        --with-libxslt \
        --with-lz4 \
        --with-zstd \
        --enable-rpath \
        --with-system-tzdata=/usr/share/zoneinfo
    make -sj"$(nproc)" world-bin
    make install-world-bin
    cd /
    rm -rf "${src_dir}"
else
    # install key and repositories
    curl -sf https://www.postgresql.org/media/keys/ACCC4CF8.asc | APT_KEY_DONT_WARN_ON_DANGEROUS_USAGE=1 apt-key add -
    echo "deb https://apt.postgresql.org/pub/repos/apt bookworm-pgdg main" >> /etc/apt/sources.list.d/postgresql.list
    echo "deb https://apt-archive.postgresql.org/pub/repos/apt bookworm-pgdg-archive main" >> /etc/apt/sources.list.d/postgresql.list

    apt-get update

    # infer the pgdgversion of postgres based on the $PG_VERSION
    pgdg_version=$(apt list -a postgresql-server-dev-${PG_MAJOR} 2>/dev/null | grep "${PG_VERSION}" | awk '{print $2}' | head -n1 )

    apt-get install -y --no-install-recommends --allow-downgrades \
        libpq-dev=${pgdg_version} \
        libpq5=${pgdg_version} \
        postgresql-${PG_MAJOR}=${pgdg_version} \
        postgresql-client-${PG_MAJOR}=${pgdg_version} \
        postgresql-${PG_MAJOR}-dbgsym=${pgdg_version} \
        postgresql-server-dev-${PG_MAJOR}=${pgdg_version}
fi

# clear apt cache
rm -rf /var/lib/apt/lists/*
EOF

# make pg_config (installed by postgresql-server-dev-${PG_MAJOR} from apt or
# by the PG19 source-build path) discoverable to extension builds
ENV PATH=/usr/lib/postgresql/$PG_MAJOR/bin/:$PATH

USER circleci
WORKDIR /home/circleci
