#!/bin/bash

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

# Usage: bin/run_tests.sh
#
# Runs tests.
#
# This should be called from inside a container and after the dependent
# services have been launched. It depends on:
#
# * elasticsearch
# * postgresql

set -euo pipefail

# Wait for services to be ready (both have the same endpoint url)
echo ">>> wait for services"
waitfor --verbose "http://${PUBSUB_EMULATOR_HOST}"
waitfor --verbose "${STORAGE_EMULATOR_HOST}/storage/v1/b"
waitfor --verbose --codes=200,404 "${SENTRY_DSN}"

# Run tests
echo ">>> pytest"
pytest $@
