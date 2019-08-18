FROM debian:buster
LABEL maintainer="Mickael Royer <mickael.royer@enac.fr>"

ENV HOME=/root VTYSH_PAGER=more TERM=vt100 PAGER=less
ADD . /build

RUN /build/prepare.sh && \
	/build/system_services.sh && \
	/build/utilities.sh && \
	/build/cleanup.sh

RUN mkdir -p /var/log/supervisor
COPY conf/supervisord.conf /etc/supervisor/conf.d/supervisord.conf
CMD ["/usr/bin/supervisord"]
