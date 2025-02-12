# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

import os
from uuid import uuid4

import pytest
from click.testing import CliRunner
from google.cloud import storage
from google.auth.credentials import AnonymousCredentials
from google.cloud.exceptions import NotFound

from obs_common.gcs_cli import gcs_group

REQUIRE_EMULATOR = pytest.mark.skipif(
    not os.environ.get("STORAGE_EMULATOR_HOST"),
    reason="test requires STORAGE_EMULATOR_HOST",
)


class GcsHelper:
    """GCS helper class.

    When used in a context, this will clean up any buckets created.

    """

    def __init__(self):
        self._buckets_seen = None
        if os.environ.get("STORAGE_EMULATOR_HOST"):
            self.client = storage.Client(
                credentials=AnonymousCredentials(),
            )
        else:
            self.client = storage.Client()

    def __enter__(self):
        self._buckets_seen = set()
        return self

    def __exit__(self, exc_type, exc_value, exc_tb):
        for bucket_name in self._buckets_seen:
            try:
                bucket = self.client.get_bucket(bucket_or_name=bucket_name)
                bucket.delete(force=True)
            except NotFound:
                pass
        self._buckets_seen = None

    def create_bucket(self, bucket_name):
        try:
            bucket = self.client.get_bucket(bucket_or_name=bucket_name)
        except NotFound:
            bucket = self.client.create_bucket(bucket_or_name=bucket_name)
        if self._buckets_seen is not None:
            self._buckets_seen.add(bucket_name)
        return bucket

    def upload(self, bucket_name, key, data):
        """Puts an object into the specified bucket."""
        bucket = self.create_bucket(bucket_name)
        bucket.blob(blob_name=key).upload_from_string(data)

    def download(self, bucket_name, key):
        """Fetches an object from the specified bucket"""
        bucket = self.create_bucket(bucket_name)
        return bucket.blob(blob_name=key).download_as_bytes()

    def list(self, bucket_name):
        """Return list of keys for objects in bucket."""
        self.create_bucket(bucket_name)
        blobs = list(self.client.list_blobs(bucket_or_name=bucket_name))
        return [blob.name for blob in blobs]


@pytest.fixture
def gcs_helper():
    with GcsHelper() as gcs_helper:
        yield gcs_helper


def test_it_runs():
    """Test whether the module loads and spits out help."""
    runner = CliRunner()
    result = runner.invoke(gcs_group, ["--help"])
    assert result.exit_code == 0


@REQUIRE_EMULATOR
def test_upload_file_to_root(gcs_helper, tmp_path):
    """Test uploading one file to a bucket root."""
    bucket = gcs_helper.create_bucket("test").name
    path = tmp_path / uuid4().hex
    path.write_text(path.name)
    result = CliRunner().invoke(
        gcs_group, ["upload", str(path.absolute()), f"gs://{bucket}"]
    )
    assert result.exit_code == 0
    assert gcs_helper.download(bucket, path.name) == path.name.encode("utf-8")


@REQUIRE_EMULATOR
def test_upload_file_to_dir(gcs_helper, tmp_path):
    """Test uploading one file to a directory inside a bucket."""
    bucket = gcs_helper.create_bucket("test").name
    path = tmp_path / uuid4().hex
    path.write_text(path.name)
    result = CliRunner().invoke(
        gcs_group, ["upload", str(path.absolute()), f"gs://{bucket}/{path.name}/"]
    )
    assert result.exit_code == 0
    assert gcs_helper.download(bucket, f"{path.name}/{path.name}") == path.name.encode(
        "utf-8"
    )


@REQUIRE_EMULATOR
def test_upload_dir_to_dir(gcs_helper, tmp_path):
    """Test uploading a whole directory to a directory inside a bucket."""
    bucket = gcs_helper.create_bucket("test").name
    path = tmp_path / uuid4().hex
    path.write_text(path.name)
    result = CliRunner().invoke(
        gcs_group, ["upload", str(tmp_path.absolute()), f"gs://{bucket}/{path.name}"]
    )
    assert result.exit_code == 0
    assert gcs_helper.download(bucket, f"{path.name}/{path.name}") == path.name.encode(
        "utf-8"
    )


@REQUIRE_EMULATOR
def test_download_file_to_file(gcs_helper, tmp_path):
    """Test downloading one file to a file with a different name."""
    bucket = "test"
    key = uuid4().hex
    gcs_helper.upload(bucket, key, key)
    path = tmp_path / uuid4().hex
    path.write_text(path.name)
    result = CliRunner().invoke(
        gcs_group, ["download", f"gs://{bucket}/{key}", str(path.absolute())]
    )
    assert result.exit_code == 0
    assert path.read_text() == key


@REQUIRE_EMULATOR
def test_download_file_to_dir(gcs_helper, tmp_path):
    """Test uploading one file to a directory."""
    bucket = "test"
    key = uuid4().hex
    gcs_helper.upload(bucket, key, key)
    path = tmp_path / key
    result = CliRunner().invoke(
        gcs_group, ["download", f"gs://{bucket}/{key}", str(tmp_path.absolute())]
    )
    assert result.exit_code == 0
    assert path.read_text() == key


@REQUIRE_EMULATOR
def test_download_root_to_dir(gcs_helper, tmp_path):
    """Test downloading a whole directory to a directory."""
    bucket = "test"
    key = uuid4().hex
    gcs_helper.upload(bucket, f"{key}/{key}", key)
    path = tmp_path / key / key
    result = CliRunner().invoke(
        gcs_group, ["download", f"gs://{bucket}", str(tmp_path.absolute())]
    )
    assert result.exit_code == 0
    assert path.read_text() == key
