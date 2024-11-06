#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

"""
Given a url, performs GET requests until it gets back an HTTP 200 or exceeds the wait
timeout.

Usage: bin/waitfor.py [--timeout T] [--verbose] [--codes CODES] URL
"""

import urllib.error
import urllib.request
from urllib.parse import urlsplit
import socket
import sys
import time

import click

DEFAULT_PORTS = {
    "amqp": 5672,
    "http": 80,
    "https": 443,
    "mysql": 3306,
    "mysql2": 3306,
    "pgsql": 5432,
    "postgres": 5432,
    "postgresql": 5432,
    "redis": 6379,
    "hiredis": 6379,
}
NOOP_PROTOCOLS = {
    "sqlite",
    "sqlite3",
}


@click.command(
    help=(
        "Performs GET requests against given URL until HTTP 200 or exceeds "
        "wait timeout."
    )
)
@click.argument("url")
@click.option("--verbose", is_flag=True)
@click.option("--conn-only", is_flag=True, help="Only check for connection.")
@click.option(
    "--codes",
    default=[200],
    multiple=True,
    show_default=True,
    type=int,
    help="Valid HTTP response codes. May be specified multiple times.",
)
@click.option(
    "--timeout",
    default=15,
    show_default=True,
    type=int,
    help=(
        "Seconds after which to stop retrying. This is separate from the timeout "
        "for individual attempts, which is 5 seconds."
    ),
)
def main(verbose, timeout, conn_only, codes, url):
    parsed_url = urlsplit(url)
    if "@" in parsed_url.netloc:
        netloc = parsed_url.netloc
        netloc = netloc[netloc.find("@") + 1 :]
        parsed_url = parsed_url._replace(netloc=netloc)
        url = parsed_url.geturl()

    if parsed_url.scheme in NOOP_PROTOCOLS:
        if verbose:
            print(f"Skipping because protocol {parsed_url.scheme} is noop")
        return

    if conn_only:
        host = parsed_url.hostname
        port = parsed_url.port or DEFAULT_PORTS.get(parsed_url.scheme, None)
        sock = (host, port)
        if verbose:
            print(f"Testing {host}:{port} for connection with timeout {timeout}...")
    elif verbose:
        print(f"Testing {url} for {codes!r} with timeout {timeout}...")

    start_time = time.time()

    last_fail = ""
    while True:
        try:
            if conn_only:
                with socket.socket() as s:
                    s.settimeout(5.0)
                    s.connect(sock)
                return
            else:
                with urllib.request.urlopen(url, timeout=5) as resp:
                    if resp.code in codes:
                        return
                    last_fail = f"HTTP status code: {resp.code}"
        except ConnectionResetError as error:
            last_fail = f"ConnectionResetError: {error}"
        except TimeoutError as error:
            last_fail = f"TimeoutError: {error}"
        except urllib.error.URLError as error:
            if hasattr(error, "code") and error.code in codes:
                return
            last_fail = f"URLError: {error}"
        except socket.gaierror as error:
            # This can mean that docker compose has not started the container, so the
            # hostname can't be resolved (i.e. DNS failure).
            # From docs https://docs.python.org/3/library/socket.html#socket.gaierror:
            # A subclass of OSError, this exception is raised for address-related errors
            # by getaddrinfo() and getnameinfo()
            last_fail = f"socket.gaierror: {error}"
        except ConnectionRefusedError as error:
            last_fail = f"ConnectionRefusedError: {error}"

        if verbose:
            print(last_fail)

        time.sleep(0.5)

        delta = time.time() - start_time
        if delta > timeout:
            raise click.ClickException(f"Failed: {last_fail}, elapsed: {delta:.2f}s")


if __name__ == "__main__":
    sys.exit(main())
