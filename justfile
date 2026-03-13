# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

_default:
    @just --list

# Build docker images.
build *args:
    docker compose --progress plain build {{args}}

# Start Docker containers.
up *args='--detach':
    docker compose up {{args}}

# Stop and remove Docker containers.
down *args:
    docker compose down {{args}}

# Lint code, or use --fix to reformat and apply auto-fixes for lint.
lint *args:
    uv run bin/lint.sh {{args}}

# Run tests.
test *args: up
    uv run bin/test.sh {{args}}
