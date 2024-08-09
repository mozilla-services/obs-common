# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.
import os
import subprocess
import sys
from pathlib import Path

import requests
import pytest
from click.testing import CliRunner
from urllib.parse import urlsplit, urlunsplit

from obs_common.sentry_wrap import cli_main


@pytest.fixture
def tmp_cwd(tmp_path):
    orig_wd = os.getcwd()
    os.chdir(tmp_path)
    try:
        yield tmp_path
    finally:
        os.chdir(orig_wd)


def test_it_runs():
    """Test whether the module loads and spits out help."""
    runner = CliRunner()
    result = runner.invoke(cli_main, ["--help"])
    assert result.exit_code == 0


@pytest.mark.skipif(not os.environ.get("SENTRY_DSN"), reason="test requires SENTRY_DSN")
def test_sentry_wrap_error_has_release(tmp_cwd):
    sentry_dsn = urlsplit(os.environ["SENTRY_DSN"])
    # remove username/password from netloc
    netloc = sentry_dsn.netloc.split("@", 1)[-1]
    fakesentry_url = urlunsplit(sentry_dsn._replace(netloc=netloc, path="/"))

    # Flush fakesentry to ensure we fetch only the desired error downstream
    requests.post(f"{fakesentry_url}api/flush/", timeout=5)

    version = tmp_cwd / "version.json"
    version.write_text('{"version":"v2024.01.01","commit":"1234567890abcdef"}')
    expected_release = "v2024.01.01:12345678"

    # NOTE(relud): use subprocess here to avoid race condition on sentry sending events
    sentry_wrap = Path(__file__).parent.parent / "obs_common" / "sentry_wrap.py"
    subprocess.run(
        [sys.executable, sentry_wrap, "wrap-process", "--", "false"],
        timeout=10,
    )

    # We don't have to worry about a race condition here, because when the
    # subprocess exits, we know the sentry_sdk sent the event, and it has
    # been processed successfully by fakesentry.
    events_resp = requests.get(f"{fakesentry_url}api/eventlist/", timeout=5)
    events_resp.raise_for_status()
    event_id = events_resp.json()["events"][0]["event_id"]
    event_resp = requests.get(f"{fakesentry_url}api/event/{event_id}", timeout=5)
    event_resp.raise_for_status()

    release = event_resp.json()["payload"]["envelope_header"]["trace"]["release"]

    assert release == expected_release
