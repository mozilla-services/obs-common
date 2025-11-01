FROM python:3.11.14-slim-bookworm@sha256:e5b49052cdc5d8223d037a718e3cecd4169f41701e03d0baf5c994bf19522bf4

ARG groupid=5000
ARG userid=5000

WORKDIR /app/

RUN groupadd -r kent && useradd --no-log-init -r -g kent kent

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN pip install -U 'pip>=20' && \
    pip install --no-cache-dir 'kent==2.0.0'

USER kent

ENTRYPOINT ["/usr/local/bin/kent-server"]
CMD ["run"]
