FROM python:3.12-slim-bookworm

# add unpriviliged user for tests
RUN useradd -ms /bin/bash circleci

RUN <<'EOF'
# install dependencies
apt-get update

apt-get install -y --no-install-recommends \
    apt-transport-https \
    autoconf \
    build-essential \
    ca-certificates \
    curl \
    debian-archive-keyring \
    gdb \
    git \
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
    lsof \
    make \
    net-tools \
    perl \

# clear apt cache
rm -rf /var/lib/apt/lists/*
EOF

# make special locales available
COPY locale.gen /etc/locale.gen
RUN locale-gen

ARG PG_VERSION
ARG PG_MAJOR
ARG PG19_SOURCE_REF
ENV PG_VERSION=$PG_VERSION
ENV PG_MAJOR=$PG_MAJOR
ENV PG19_SOURCE_REF=$PG19_SOURCE_REF

RUN <<'EOF'
# install postgres ecosystem for pg version: $PG_VERSION

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

    # apt-installed postgres packages normally create this user/group; do
    # it manually for the source-build path so the chown in the next RUN
    # step still works.
    if ! getent group postgres >/dev/null; then
        groupadd --system postgres
    fi
    if ! id postgres >/dev/null 2>&1; then
        useradd --system --gid postgres --home-dir /var/lib/postgresql --shell /bin/bash postgres
    fi
    mkdir -p /var/lib/postgresql
    chown -R postgres:postgres /var/lib/postgresql
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
        postgresql-server-dev-${PG_MAJOR}=${pgdg_version} \

fi

# clear apt cache
rm -rf /var/lib/apt/lists/*
EOF

# add postgress to the path
ENV PATH=/usr/lib/postgresql/$PG_MAJOR/bin/:$PATH

# setup /var/run/postgresql for use with circleci
RUN mkdir -p /var/run/postgresql && chown -R postgres:postgres /var/run/postgresql && chmod 2777 /var/run/postgresql

COPY ./files/etc/requirements.txt /tmp/etc/
RUN <<EOF
set -eux

pip3 install -Ir /tmp/etc/requirements.txt

MITMDUMP_BIN="$(python3 -c 'import sysconfig, pathlib; print(pathlib.Path(sysconfig.get_path("scripts")) / "mitmdump")')"

if [ ! -x "$MITMDUMP_BIN" ]; then
    echo "mitmdump executable not found at $MITMDUMP_BIN" >&2
    exit 1
fi

if [ "$MITMDUMP_BIN" != "/usr/local/bin/mitmdump" ]; then
    ln -sf "$MITMDUMP_BIN" /usr/local/bin/mitmdump
fi

hash mitmdump
EOF

WORKDIR /home/circleci
