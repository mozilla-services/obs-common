# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at https://mozilla.org/MPL/2.0/.

from click.testing import CliRunner

from obs_common import license_check


def test_it_runs():
    """Test whether the module loads and spits out help."""
    runner = CliRunner()
    result = runner.invoke(license_check.main, ["--help"])
    assert result.exit_code == 0


def test_license_present(tmp_path):
    target = tmp_path / "target.py"
    target.write_text(
        "# This Source Code Form is subject to the terms of the Mozilla Public\n"
        "# License, v. 2.0. If a copy of the MPL was not distributed with this\n"
        "# file, You can obtain one at https://mozilla.org/MPL/2.0/.\n"
    )
    runner = CliRunner()
    result = runner.invoke(license_check.main, [str(target)])
    assert result.exit_code == 0


def test_license_missing(tmp_path):
    target = tmp_path / "target.py"
    target.touch()
    runner = CliRunner()
    result = runner.invoke(license_check.main, [str(target)])
    assert result.exit_code == 0
