FROM debian:buster
LABEL maintainer="mickael.royer@enac.fr"

ENV HOME=/root VTYSH_PAGER=more TERM=vt100 PAGER=less
ADD . /build

RUN /build/prepare.sh && \
	/build/system_services.sh && \
	/build/utilities.sh && \
	/build/cleanup.sh
COPY ./dhclient-nodnsupdate /etc/dhcp/dhclient-enter-hooks.d/nodnsupdate
RUN chmod +x /etc/dhcp/dhclient-enter-hooks.d/nodnsupdate

CMD ["/usr/bin/iinit.py"]
