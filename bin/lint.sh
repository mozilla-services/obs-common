#!/bin/bash

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

# Usage: bin/run_lint.sh [--fix]
#
# Runs linting and code fixing.
#
# This should be called from inside a container or venv.

set -euo pipefail

FILES="bin obs_common tests"
PYTHON_VERSION=$(python --version)


if [[ "${1:-}" == "--fix" ]]; then
    echo ">>> ruff fix (${PYTHON_VERSION})"
    ruff format $FILES
    ruff check --fix $FILES

else
    echo ">>> ruff (${PYTHON_VERSION})"
    ruff check $FILES
    ruff format --check $FILES

    echo ">>> license check (${PYTHON_VERSION})"
    if [[ -d ".git" ]]; then
        # If the .git directory exists, we can let license-check do
        # git ls-files.
        license-check
    else
        # The .git directory doesn't exist, so run it on all the Python
        # files in the tree.
        license-check .
    fi
fi