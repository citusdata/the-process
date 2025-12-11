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

curl -L "https://github.com/citusdata/tools/archive/v${TOOLS_VERSION}.tar.gz" | tar xz
cd "tools-${TOOLS_VERSION}"
make uncrustify/.install
cd ..
rm -rf "v${TOOLS_VERSION}.tar.gz"

curl -L "https://github.com/uncrustify/uncrustify/archive/uncrustify-0.82.0.tar.gz" | tar xz
cd uncrustify-uncrustify-0.82.0/
mkdir build
cd build
cmake ..
make -j5
make install
cd ../..
rm -rf uncrustify-uncrustify-0.82.0/

# this image is only used for testing purposes, so should be okay to overwrite system-managed packages
pip3 install -Ir /tmp/etc/requirements.txt --break-system-packages
apk del installdeps
EOF
