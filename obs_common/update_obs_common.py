# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import re
import sys
from pathlib import Path

import requests

REQUIREMENT_PATTERN = re.compile("^obs-common @ https://.*$", re.MULTILINE)


def main():
    latest_release = requests.get(
        "https://api.github.com/repos/mozilla-services/obs-common/releases/latest",
        timeout=5,
    ).json()
    assets_url = latest_release["assets_url"]
    assets = requests.get(assets_url, timeout=5).json()
    for asset in assets:
        if asset["name"].endswith(".whl"):
            break
    else:
        print("could not find wheel in latest release assets", file=sys.stderr)
        return 1
    download_url = asset["browser_download_url"]
    req_in = Path("requirements.in")
    req_in_text = req_in.read_text()
    if download_url in req_in_text:
        return 0
    if not REQUIREMENT_PATTERN.findall(req_in_text):
        print("could not find obs-common in requirements.in")
        return 1
    req_in.write_text(
        REQUIREMENT_PATTERN.sub(f"obs-common @ {download_url}", req_in_text, count=1)
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
