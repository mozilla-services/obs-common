# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import subprocess
from datetime import datetime


def generate_tag():
    """Generate a release tag based on the current date.

    If the release tag already exists in git, add a monotonically increasing integer
    suffix separated by a dash.

    For example:

        "v2024.07.01"
        "v2024.07.01-1"
        "v2024.07.01-2"
    """
    base_tag_name = datetime.now().strftime("v%Y.%m.%d")
    existing_tags = subprocess.check_output(
        ["git", "tag", "-l", base_tag_name, f"{base_tag_name}-*"]
    )
    tag_indices = set()
    for tag in existing_tags.decode("utf-8").split("\n"):
        if not tag:
            continue
        if "-" not in tag:
            tag_indices.add(0)
        try:
            tag_indices.add(int(tag.split("-", 1)[-1]))
        except ValueError:
            continue
    last_tag = max(tag_indices, default=None)
    if last_tag is None:
        return base_tag_name
    return f"{base_tag_name}-{last_tag + 1}"
