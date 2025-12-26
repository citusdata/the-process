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
      openssl-dev \
      py3-pip \
      python3-dev \
      tar \
      llvm21 \
      llvm21-dev \
      llvm21-libs \
      llvm21-linker-tools \
      llvm21-static \
      clang \
      elfutils-dev \
      zlib-dev \
      zlib-static \
      libxml2-static \
      xz-static \
      zstd-static

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
export RUSTUP_HOME="${RUSTUP_HOME:-/root/.rustup}"

curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --profile minimal --default-host x86_64-unknown-linux-musl
. "$CARGO_HOME/env"
rustup toolchain install nightly-x86_64-unknown-linux-musl
rustup component add rust-src --toolchain nightly-x86_64-unknown-linux-musl
cargo install --locked bpf-linker --no-default-features --features llvm-21
export PATH="/root/.cargo/bin:${PATH}"

LLVM_CONFIG="$(command -v llvm-config || command -v llvm-config-21)"
LLVM_LIBDIR="$(${LLVM_CONFIG} --libdir)"
LLVM_PREFIX="$(dirname "${LLVM_LIBDIR}")"
export LD_LIBRARY_PATH="${LLVM_LIBDIR}:${LD_LIBRARY_PATH:-}"
export PKG_CONFIG_PATH="${LLVM_LIBDIR}/pkgconfig:${PKG_CONFIG_PATH:-}"
export LLVM_SYS_211_PREFIX="${LLVM_SYS_211_PREFIX:-${LLVM_PREFIX}}"
export LLVM_SYS_211_STATIC=1
export AYA_RUSTC_LLVM_PROXY_DISABLE_DLOPEN=1
export AYA_RUSTC_LLVM_PROXY_LIB_DIR="${LLVM_LIBDIR}"


install -m 755 "$CARGO_HOME/bin/bpf-linker" /usr/local/bin/bpf-linker

# this image is only used for testing purposes, so should be okay to overwrite system-managed packages
pip3 install -Ir /tmp/etc/requirements.txt --break-system-packages
apk del installdeps
EOF
