# This should be kept in sync with the python version used in .devcontainer/Dockerfile and
# docker/images/fakesentry/Dockerfile
FROM --platform=linux/amd64 ghcr.io/astral-sh/uv:python3.11-bookworm-slim@sha256:4f5d923c9dcea037f57bda425dd209f3ec643da2f0b74227f68d09dab0b3bb36

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

USER app

COPY --chown=app:app . /app

# Install Python dependencies
RUN --mount=type=cache,uid=$userid,gid=$groupid,target=/home/app/.cache/uv \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync
ENV PATH="/app/.venv/bin:$PATH"

CMD ["/bin/bash"]
