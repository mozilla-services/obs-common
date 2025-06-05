# This should be kept in sync with the python version used in .devcontainer/Dockerfile and
# docker/images/fakesentry/Dockerfile
FROM --platform=linux/amd64 python:3.11.12-slim-bookworm@sha256:dbf1de478a55d6763afaa39c2f3d7b54b25230614980276de5cacdde79529d0c

# Set up user and group
ARG groupid=10001
ARG userid=10001

WORKDIR /app/
RUN groupadd --gid $groupid app && \
    useradd -g app --uid $userid --shell /usr/sbin/nologin --create-home app && \
    chown app:app /app/

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        git \
        ripgrep \
        tig && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/* /tmp/* /var/tmp/*

# Install Python dependencies
COPY --chown=app:app requirements.txt /app/

RUN pip install -U 'pip>=20' && \
    pip install --no-cache-dir --no-deps --only-binary :all: -r requirements.txt && \
    pip install --no-cache-dir ipython && \
    pip check --disable-pip-version-check

COPY --chown=app:app . /app

ARG version=1.0
RUN SETUPTOOLS_SCM_PRETEND_VERSION_FOR_OBS_COMMON=${version} pip install -e . --no-deps

USER app

CMD ["/bin/bash"]
