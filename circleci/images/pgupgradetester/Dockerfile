FROM python:3.12-slim-bookworm

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
    make \
    perl \

# clear apt cache
rm -rf /var/lib/apt/lists/*
EOF

ARG PG_VERSIONS
ARG PG19_SOURCE_REF
ENV PG_VERSIONS=$PG_VERSIONS
ENV PG19_SOURCE_REF=$PG19_SOURCE_REF

# Hacky way to fetch all the pgdg versions so we can pin them
# you will find the sequence '"'"' a couple of times. This is to
# insert a ' character into the -c argument to bash.
# The reason for this convoluted way of installing postgres is
# because docker uses /bin/sh to execute the RUN commands where
# the below code requires /bin/bash.
SHELL ["/bin/bash", "-c"]
RUN <<'EOF'
# install postgres ecosystem for pg versions: $PG_VERSIONS
set -eux

# install key and repositories
curl -sf https://www.postgresql.org/media/keys/ACCC4CF8.asc | APT_KEY_DONT_WARN_ON_DANGEROUS_USAGE=1 apt-key add -
echo "deb https://apt.postgresql.org/pub/repos/apt bookworm-pgdg main" >> /etc/apt/sources.list.d/postgresql.list
echo "deb https://apt-archive.postgresql.org/pub/repos/apt bookworm-pgdg-archive main" >> /etc/apt/sources.list.d/postgresql.list

apt-get update

pkgs=();
source_build_majors=();
for PG_VERSION in $PG_VERSIONS; do
    PG_MAJOR=$(echo ${PG_VERSION} | awk -F'[^0-9]*' '/[0-9]/ { print $1 }')
    if [ "${PG_MAJOR}" = "19" ]; then
        # PG19 is unreleased; fall through to a source build below instead
        # of asking apt for it.
        source_build_majors+=("${PG_MAJOR}");
        continue;
    fi
    pgdg_version=$(apt list -a postgresql-server-dev-${PG_MAJOR} 2>/dev/null | grep "${PG_VERSION}" | awk '{print $2}' | head -n1 )
    pkgs+=("postgresql-${PG_MAJOR}=${pgdg_version}")
    pkgs+=("postgresql-client-${PG_MAJOR}=${pgdg_version}")
    pkgs+=("postgresql-${PG_MAJOR}-dbgsym=${pgdg_version}")
    pkgs+=("postgresql-server-dev-${PG_MAJOR}=${pgdg_version}")
    last_pgdg_version=$pgdg_version;
done;

if [ ${#pkgs[@]} -gt 0 ]; then
    pkgs+=("libpq-dev=${last_pgdg_version}");
    pkgs+=("libpq5=${last_pgdg_version}");

    echo ${pkgs[@]}

    apt-get install -y --no-install-recommends --allow-downgrades \
      postgresql-common \
      ${pkgs[@]} \

fi

# Source-build any majors that aren't on apt.postgresql.org (currently PG19).
if [ ${#source_build_majors[@]} -gt 0 ]; then
    apt-get install -y --no-install-recommends \
        bison \
        flex \
        libicu-dev \
        liblz4-dev \
        libreadline-dev \
        libssl-dev \
        libxml2-dev \
        libxslt-dev \
        libzstd-dev \
        pkg-config \
        zlib1g-dev

    if ! getent group postgres >/dev/null; then
        groupadd --system postgres
    fi
    if ! id postgres >/dev/null 2>&1; then
        useradd --system --gid postgres --home-dir /var/lib/postgresql --shell /bin/bash postgres
    fi
    mkdir -p /var/lib/postgresql
    chown -R postgres:postgres /var/lib/postgresql

    for PG_MAJOR in "${source_build_majors[@]}"; do
        src_dir=/tmp/pg${PG_MAJOR}-src
        rm -rf "${src_dir}"
        mkdir -p "${src_dir}"
        curl -fsL "https://codeload.github.com/postgres/postgres/tar.gz/${PG19_SOURCE_REF}" \
            | tar -xzf - -C "${src_dir}" --strip-components=1
        pushd "${src_dir}"
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
        popd
        rm -rf "${src_dir}"
    done
fi

# clear apt cache
rm -rf /var/lib/apt/lists/*
EOF

# setup /var/run/postgresql for use with circleci
RUN mkdir -p /var/run/postgresql && chown -R postgres:postgres /var/run/postgresql && chmod 2777 /var/run/postgresql

COPY ./files/etc/requirements.txt /tmp/etc/
RUN pip3 install -Ir /tmp/etc/requirements.txt
