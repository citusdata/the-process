FROM python:3.6-slim-stretch

ARG PG_MAJOR
ENV PG_MAJOR $PG_MAJOR

COPY files /tmp

RUN set -ex; \
	ln -s /tmp/sbin/* /usr/local/sbin/; \
	ln -s /tmp/bin/* /usr/local/bin; \
	install-testdeps

RUN mkdir -p /var/run/postgresql && chown -R postgres:postgres /var/run/postgresql && chmod 2777 /var/run/postgresql

WORKDIR /home/circleci
