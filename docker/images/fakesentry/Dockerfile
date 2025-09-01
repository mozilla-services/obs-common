FROM python:3.11.13-slim-bookworm@sha256:838ff46ae6c481e85e369706fa3dea5166953824124735639f3c9f52af85f319

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
