# buildpack-deps:stretch
FROM buildpack-deps@sha256:19a482aad09128bd0c448373d933aa0f108dc8eb9be2317dca3797c646ce4b57

COPY files /tmp

RUN set -ex; \
	ln -s /tmp/sbin/* /usr/local/sbin/; \
	ln -s /tmp/bin/* /usr/local/bin/; \
	ln -s /tmp/etc/* /etc/dpkg/dpkg.cfg.d/; \
	install-extdeps

USER circleci
WORKDIR /home/circleci
