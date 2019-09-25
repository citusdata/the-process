FROM python:3.6-slim-stretch

COPY files /tmp

RUN set -ex; \
	ln -s /tmp/sbin/* /usr/local/sbin/; \
	ln -s /tmp/bin/* /usr/local/bin; \
	install-testdeps

WORKDIR /home/circleci
