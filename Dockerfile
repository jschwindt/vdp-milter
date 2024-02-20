#Dockerfile for a milter service
FROM debian:latest

RUN apt-get update \
    && apt-get -y --no-install-recommends install \
        tini \
        python3-milter \
        python3-redis \
        python3-pip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

COPY vdp-milter.py /

EXPOSE 9000/tcp

ENTRYPOINT ["/usr/bin/tini", "--"]

CMD ["/usr/bin/python3", "-u", "/vdp-milter.py"]
