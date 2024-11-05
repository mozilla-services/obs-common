#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
This script looks at the ``/__version__`` endpoint information and tells you
how far behind different server environments are from main tip.
"""

import json
import sys
from urllib.parse import urlparse
from urllib.request import urlopen
from pathlib import Path

import click
import tomllib


DESCRIPTION = """
Report how far behind different server environments are from main tip.

For options that are not specified, values are pulled from the [tool.service-status]
section in the pyproject.toml file in the current working directory, if it exists.
"""


def fetch(url, is_json=True):
    """Fetch data from a url

    This raises URLError on HTTP request errors. It also raises JSONDecode
    errors if it's not valid JSON.

    """
    if not url.startswith(("http:", "https:")):
        raise ValueError("URL must start with 'http:' or 'https:'")
    # NOTE(willkg): ruff S310 can't determine whether we've validated the url or not
    fp = urlopen(url, timeout=5)  # noqa: S310
    data = fp.read()
    if is_json:
        return json.loads(data)
    return data


def fetch_history_from_github(main_branch, user, repo, from_sha):
    return fetch(
        "https://api.github.com/repos/%s/%s/compare/%s...%s"
        % (user, repo, from_sha, main_branch)
    )


class StdoutOutput:
    def section(self, name):
        print("")
        print("%s" % name)
        print("=" * len(name))
        print("")

    def row(self, *args):
        template = "%-13s " * len(args)
        print("  " + template % args)

    def print_delta(self, main_branch, user, repo, sha):
        resp = fetch_history_from_github(main_branch, user, repo, sha)
        # from pprint import pprint
        # pprint(resp)
        if resp["total_commits"] == 0:
            self.row("", "status", "identical")
        else:
            self.row("", "status", "%s commits" % resp["total_commits"])
            self.row()
            self.row(
                "",
                "https://github.com/%s/%s/compare/%s...%s"
                % (
                    user,
                    repo,
                    sha[:8],
                    main_branch,
                ),
            )
            self.row()
            for i, commit in enumerate(resp["commits"]):
                if len(commit["parents"]) > 1:
                    # Skip merge commits
                    continue

                self.row(
                    "",
                    commit["sha"][:8],
                    ("HEAD: " if i == 0 else "")
                    + "%s (%s)"
                    % (
                        commit["commit"]["message"].splitlines()[0][:60],
                        (commit["author"] or {}).get("login", "?")[:10],
                    ),
                )
        self.row()


@click.command(help=DESCRIPTION)
@click.option(
    "--main-branch",
    help=(
        "The name of the main branch in the git repository. Defaults "
        'to "main" if not configured in pyproject.toml.'
    ),
)
@click.option(
    "--host",
    "hosts",
    multiple=True,
    help=(
        "A list of hosts which have a ``/__version__`` Dockerflow endpoint in the "
        "form of ENVIRONMENTNAME=HOST."
    ),
)
def main(main_branch, hosts):
    config_data = {}
    if (pyproject_toml := Path("pyproject.toml")).exists():
        data = tomllib.loads(pyproject_toml.read_text())
        config_data = data.get("tool", {}).get("service-status", {})

    if main_branch is None:
        main_branch = config_data.get("main_branch", "main")

    if not hosts:
        if "hosts" in config_data:
            hosts = config_data["hosts"]
        else:
            raise click.ClickException("no hosts configured")

    out = StdoutOutput()

    current_section = ""

    for line in hosts:
        parts = line.split("=", 1)
        if len(parts) == 1:
            service = parts[0]
            env_name = "environment"
        else:
            env_name, service = parts

        if current_section != env_name:
            out.section(env_name)
            current_section = env_name

        service = service.rstrip("/")
        resp = fetch(f"{service}/__version__")
        commit = resp["commit"]
        tag = resp.get("version") or "(none)"

        parsed = urlparse(resp["source"])
        _, user, repo = parsed.path.split("/")
        service_name = repo
        out.row(service_name, "version", commit, tag)
        out.print_delta(main_branch, user, repo, commit)


if __name__ == "__main__":
    sys.exit(main())
