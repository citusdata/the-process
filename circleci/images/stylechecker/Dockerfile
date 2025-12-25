# we cannot easily upgrade to python 3.11 as our mitmproxy fork does not ship with it
FROM alpine:latest
ARG TOOLS_VERSION

COPY ./files/etc/requirements.txt /tmp/etc/
# openssh is needed in the image for CircleCI to pull the repo over ssh
RUN <<'EOF'
# install dependencies
set -eux

apk add --no-cache --virtual installdeps \
      curl \
      make \
      cmake \
      g++ \
      gcc \
      gzip \
      musl-dev \
      cargo \
      rust \
      openssl-dev \
      py3-pip \
      python3-dev \
      tar \

apk add --no-cache \
      ca-certificates \
      bash \
      git \
      grep \
      openssh \
      perl \
      python3 \
      py3-packaging \

curl -fsSL "https://codeload.github.com/citusdata/tools/tar.gz/v${TOOLS_VERSION}" | tar xz
cd "tools-${TOOLS_VERSION}"
make uncrustify/.install
cd ..
rm -rf "v${TOOLS_VERSION}.tar.gz"

curl -fsSL "https://codeload.github.com/uncrustify/uncrustify/tar.gz/uncrustify-0.82.0" | tar xz
cd uncrustify-uncrustify-0.82.0/
mkdir build
cd build
cmake ..
make -j5
make install
cd ../..
rm -rf uncrustify-uncrustify-0.82.0/

export CARGO_HOME="${CARGO_HOME:-/root/.cargo}"
cargo install --locked bpf-linker
install -m 755 "$CARGO_HOME/bin/bpf-linker" /usr/local/bin/bpf-linker

# this image is only used for testing purposes, so should be okay to overwrite system-managed packages
pip3 install -Ir /tmp/etc/requirements.txt --break-system-packages
apk del installdeps
EOF
