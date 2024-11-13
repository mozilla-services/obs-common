# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

_default:
  @just --list

# Build docker images.
build *args:
  docker compose --progress plain build {{args}}

# Open a shell in docker.
shell *args:
  docker compose run --rm shell {{args}}

# Run VS Code development container.
devcontainer:
  docker compose up --detach devcontainer

# Rebuild requirements.txt file after requirements.in changes.
rebuild-reqs *args:
  docker compose run --rm --no-deps shell pip-compile --allow-unsafe --generate-hashes --strip-extras {{args}}

# Lint code, or use --fix to reformat and apply auto-fixes for lint.
lint *args:
  docker compose run --rm --no-deps shell bin/lint.sh {{args}}

# Run tests.
test *args:
  docker compose run --rm shell bin/test.sh {{args}}
