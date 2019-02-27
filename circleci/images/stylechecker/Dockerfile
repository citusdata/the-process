FROM alpine:3.9
ARG TOOLS_VERSION=0.7.9

RUN apk add --no-cache --virtual installdeps curl make && \
    apk add --no-cache \
        ca-certificates \
        git \
        gzip \
        openssh \
        perl \
        tar \
        uncrustify && \
    curl -sfLO "https://github.com/citusdata/tools/archive/v${TOOLS_VERSION}.tar.gz" && \
    tar xzf "v${TOOLS_VERSION}.tar.gz" && \
    cd "tools-${TOOLS_VERSION}" && \
    make uncrustify/.install && \
    cd .. && \
    rm -rf "citus-${VERSION}" "v${TOOLS_VERSION}.tar.gz" && \
    apk del installdeps
