FROM buildpack-deps@sha256:19a482aad09128bd0c448373d933aa0f108dc8eb9be2317dca3797c646ce4b57

ARG PG_MAJOR
ENV PG_MAJOR $PG_MAJOR

COPY files /tmp

RUN set -ex; \	
	ln -s /tmp/sbin/* /usr/local/sbin/; \
	ln -s /tmp/bin/* /usr/local/bin; \
	install-testdeps

RUN mkdir -p /var/run/postgresql && chown -R postgres:postgres /var/run/postgresql && chmod 2777 /var/run/postgresql

WORKDIR /home/circleci
