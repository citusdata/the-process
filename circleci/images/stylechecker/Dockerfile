FROM alpine:3.9
ARG TOOLS_VERSION

RUN apk add --no-cache --virtual installdeps curl make sed && \
    apk add --no-cache \
        ca-certificates \
        bash \
        git \
        grep \
        gzip \
        openssh \
        perl \
        tar \
        uncrustify && \
    curl -sfLO "https://github.com/citusdata/tools/archive/v${TOOLS_VERSION}.tar.gz" && \
    tar xzf "v${TOOLS_VERSION}.tar.gz" && \
    cd "tools-${TOOLS_VERSION}" && \
    sed -i -e's/align_number_left/align_number_right/g' uncrustify/citus-style.cfg && \
    make uncrustify/.install && \
    cd .. && \
    rm -rf "citus-${VERSION}" "v${TOOLS_VERSION}.tar.gz" && \
    apk del installdeps
