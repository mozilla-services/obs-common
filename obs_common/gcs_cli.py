#!/usr/bin/env python

# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

# Manipulate emulated GCS storage.

# Usage: ./bin/gcs_cli.py CMD

import os
from pathlib import Path, PurePosixPath

import click

from google.auth.credentials import AnonymousCredentials
from google.cloud import storage
from google.cloud.exceptions import Conflict, NotFound


def get_client():
    if "STORAGE_EMULATOR_HOST" not in os.environ:
        raise click.ClickException(
            "STORAGE_EMULATOR_HOST must point to gcs emulator, but it's not set."
        )
    return storage.Client(credentials=AnonymousCredentials())


@click.group()
def gcs_group():
    """Local dev environment GCS manipulation script"""


@gcs_group.command("create")
@click.argument("bucket_name")
def create_bucket(bucket_name):
    """Creates a bucket

    Specify BUCKET_NAME.

    """
    client = get_client()

    try:
        client.create_bucket(bucket_name)
    except Conflict:
        click.echo(f"GCS bucket {bucket_name!r} already exists.")
    else:
        click.echo(f"GCS bucket {bucket_name!r} created.")


@gcs_group.command("delete")
@click.argument("bucket_name")
def delete_bucket(bucket_name):
    """Deletes a bucket

    Specify BUCKET_NAME.

    """
    client = get_client()

    bucket = None

    try:
        bucket = client.get_bucket(bucket_name)
    except NotFound:
        click.echo(f"GCS bucket {bucket_name!r} does not exist.")
        return

    # delete blobs before deleting bucket, because bucket.delete(force=True) doesn't
    # work if there are more than 256 blobs in the bucket.
    for blob in bucket.list_blobs():
        blob.delete()

    bucket.delete()
    click.echo(f"GCS bucket {bucket_name!r} deleted.")


@gcs_group.command()
@click.option("--details/--no-details", default=True, type=bool, help="With details")
def list_buckets(details):
    """List GCS buckets"""

    client = get_client()

    buckets = client.list_buckets()
    for bucket in buckets:
        if details:
            # https://cloud.google.com/storage/docs/json_api/v1/buckets#resource-representations
            click.echo(f"{bucket.name}\t{bucket.time_created}")
        else:
            click.echo(f"{bucket.name}")


@gcs_group.command()
@click.option("--details/--no-details", default=True, type=bool, help="With details")
@click.argument("bucket_name")
def list_objects(bucket_name, details):
    """List contents of a bucket"""

    client = get_client()

    try:
        client.get_bucket(bucket_name)
    except NotFound:
        click.echo(f"GCS bucket {bucket_name!r} does not exist.")
        return

    blobs = list(client.list_blobs(bucket_name))
    if blobs:
        for blob in blobs:
            # https://cloud.google.com/storage/docs/json_api/v1/objects#resource-representations
            if details:
                click.echo(f"{blob.name}\t{blob.size}\t{blob.updated}")
            else:
                click.echo(f"{blob.name}")
    else:
        click.echo("No objects in bucket.")


@gcs_group.command()
@click.argument("source")
@click.argument("destination")
def upload(source, destination):
    """Upload files to a bucket

    SOURCE is a path to a file or directory of files. will recurse on directory trees.

    DESTINATION is a path to a file or directory in the bucket, for example
    "gs://bucket/dir/" or "gs://bucket/path/to/file". If SOURCE is a directory or DESTINATION
    ends with "/", then DESTINATION is treated as a directory.
    """

    client = get_client()

    # remove protocol from destination if present
    destination = destination.split("://", 1)[-1]
    bucket_name, _, prefix = destination.partition("/")
    prefix_path = PurePosixPath(prefix)

    try:
        bucket = client.get_bucket(bucket_name)
    except NotFound as e:
        raise click.ClickException(f"GCS bucket {bucket_name!r} does not exist.") from e

    source_path = Path(source)
    if not source_path.exists():
        raise click.ClickException(f"local path {source!r} does not exist.")
    source_is_dir = source_path.is_dir()
    if source_is_dir:
        sources = [p for p in source_path.rglob("*") if not p.is_dir()]
    else:
        sources = [source_path]
    if not sources:
        raise click.ClickException(f"No files in directory {source!r}.")
    for path in sources:
        if source_is_dir:
            # source is a directory so treat destination as a directory
            key = str(prefix_path / path.relative_to(source_path))
        elif prefix == "" or prefix.endswith("/"):
            # source is a file but destination is a directory, preserve file name
            key = str(prefix_path / path.name)
        else:
            key = prefix
        blob = bucket.blob(key)
        blob.upload_from_filename(path)
        click.echo(f"Uploaded gs://{bucket_name}/{key}")


@gcs_group.command()
@click.argument("source")
@click.argument("destination")
def download(source, destination):
    """Download files from a bucket

    SOURCE is a path to a file or directory in the bucket, for example
    "gs://bucket/path/to/file" or "gs://bucket/dir/". Must end in "/" to indicate a
    directory. Will recurse on directory trees.

    DESTINATION is a path to a file or directory on the local filesystem. If SOURCE is a
    directory or DESTINATION ends with "/", then DESTINATION is treated as a directory.
    """

    client = get_client()

    # remove protocol from source if present, then separate bucket and prefix
    bucket_name, _, prefix = source.split("://", 1)[-1].partition("/")
    prefix_path = PurePosixPath(prefix)

    try:
        bucket = client.get_bucket(bucket_name)
    except NotFound as e:
        raise click.ClickException(f"GCS bucket {bucket_name!r} does not exist.") from e

    source_is_dir = not prefix or prefix.endswith("/")
    if source_is_dir:
        sources = [
            # NOTE(relud): blob.download_to_filename hangs for blobs returned by
            # list_blobs, so create a new blob object
            bucket.blob(blob.name)
            for blob in bucket.list_blobs(prefix=prefix)
        ]
        if not sources:
            raise click.ClickException(f"No keys in {source!r}.")
    else:
        sources = [bucket.blob(prefix)]

    destination_path = Path(destination)
    for blob in sources:
        if source_is_dir:
            # source is a directory so treat destination as a directory
            path = destination_path / PurePosixPath(blob.name).relative_to(prefix_path)
        elif destination_path.is_dir():
            # source is a file but destination is a directory, preserve file name
            path = destination_path / prefix_path.name
        else:
            path = destination_path
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            blob.download_to_filename(str(path))
        except NotFound as e:
            raise click.ClickException(f"GCS blob does not exist: {source!r}") from e
        click.echo(f"Downloaded gs://{bucket_name}/{blob.name}")


if __name__ == "__main__":
    gcs_group()
