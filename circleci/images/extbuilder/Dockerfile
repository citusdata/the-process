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
    curl \
    debian-archive-keyring \
    gcc \
    gnupg \
    gosu \
    libcurl4 \
    libcurl4-openssl-dev \
    libpq5 \
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
ENV PG_VERSION=$PG_VERSION
ENV PG_MAJOR=$PG_MAJOR

RUN <<'EOF'
# install postgres ecosystem for pg version: $PG_VERSION
set -eux

# install key and repositories
curl -sf https://www.postgresql.org/media/keys/ACCC4CF8.asc | APT_KEY_DONT_WARN_ON_DANGEROUS_USAGE=1 apt-key add -
echo "deb https://apt.postgresql.org/pub/repos/apt bullseye-pgdg main" >> /etc/apt/sources.list.d/postgresql.list
echo "deb https://apt-archive.postgresql.org/pub/repos/apt bullseye-pgdg-archive main" >> /etc/apt/sources.list.d/postgresql.list

# # bring in the 18 devel/beta packages
echo "deb https://apt.postgresql.org/pub/repos/apt bullseye-pgdg-testing main 18" >> /etc/apt/sources.list.d/pgdg-testing.list

apt-get update

# infer the pgdgversion of postgres based on the $PG_VERSION
pgdg_version=$(apt list -a postgresql-server-dev-${PG_MAJOR} 2>/dev/null | grep "${PG_VERSION}" | awk '{print $2}' | head -n1 )

apt-get install -y --no-install-recommends --allow-downgrades \
    libpq-dev=${pgdg_version} \
#   libpq5=${pgdg_version} \
    postgresql-${PG_MAJOR}=${pgdg_version} \
    postgresql-client-${PG_MAJOR}=${pgdg_version} \
    postgresql-${PG_MAJOR}-dbgsym=${pgdg_version} \
    postgresql-server-dev-${PG_MAJOR}=${pgdg_version}

# clear apt cache
rm -rf /var/lib/apt/lists/*
EOF

USER circleci
WORKDIR /home/circleci
