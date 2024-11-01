# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

# Include .env and export it so variables set in there are available
# in Makefile.
include .env
export

.DEFAULT_GOAL := help
.PHONY: help
help:
	@echo "Usage: make RULE"
	@echo ""
	@grep -E '^[a-zA-Z0-9_-]+:.*?## .*$$' Makefile \
	  | grep -v grep \
	    | sed -n 's/^\(.*\): \(.*\)##\(.*\)/\1\3/p' \
	    | column -t  -s '|'
	@echo ""
	@echo "Adjust your .env file to set configuration."

.docker-build:
	make build

.env:
	touch .env

.PHONY: build
build: .env  ## | Build docker images.
	docker compose --progress plain build
	touch .docker-build

.PHONY: shell
shell: .env .docker-build  ## | Open a shell in docker.
	docker compose run --rm shell

.PHONY: devcontainer
devcontainer: .env .docker-build  ## | Run VS Code development container.
	docker compose up --detach devcontainer

.PHONY: rebuildreqs
rebuildreqs: .env .docker-build  ## | Rebuild requirements.txt file after requirements.in changes.
	docker compose run --rm --no-deps shell pip-compile --allow-unsafe --generate-hashes --strip-extras --quiet

.PHONY: lint
lint: .env .docker-build  ## | Lint code.
	docker compose run --rm --no-deps shell bin/lint.sh

.PHONY: lintfix
lintfix: .env .docker-build  ## | Reformat code.
	docker compose run --rm --no-deps shell bin/lint.sh --fix

.PHONY: test
test: .env .docker-build  ## | Run tests.
	docker compose run --rm shell bin/test.sh
