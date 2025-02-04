# Copyright (C) 2025 Henrik Wilhelmsen.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at <https://mozilla.org/MPL/2.0/>.

"""Maya tests."""

import os
from pathlib import Path

import pytest

from devin.dcc.maya import get_maya, get_maya_install_dir, get_mayapy


@pytest.fixture(name="maya_version")
def fixture_maya_version() -> str:
    """Get the Maya version from environment."""
    maya_version = os.environ.get("MAYA_VERSION")
    if maya_version is None:
        pytest.fail(reason="MAYA_VERSION variable not set")

    return maya_version


@pytest.fixture(name="maya_install_dir")
def fixture_maya_install_dir(maya_version: str) -> Path | None:
    """Get the Maya install dir."""
    return get_maya_install_dir(maya_version)


@pytest.fixture(name="maya")
def fixture_maya(maya_version: str) -> Path | None:
    """Get the Maya executable path."""
    return get_maya(maya_version)


@pytest.fixture(name="mayapy")
def fixture_mayapy(maya_version: str) -> Path | None:
    """Get the mayapy executable path."""
    return get_mayapy(maya_version)


@pytest.mark.skipif(
    os.environ.get("MAYA_VERSION") is None,
    reason="MAYA_VERSION not set",
)
def test_maya_install_dir_is_dir(maya_install_dir: Path | None) -> None:
    """Test that the install dir is a directory."""
    if maya_install_dir is not None:
        assert maya_install_dir.is_dir()
    else:
        pytest.fail(reason="Maya install dir was None")


@pytest.mark.skipif(
    os.environ.get("MAYA_VERSION") is None,
    reason="MAYA_VERSION not set",
)
def test_maya_is_file(maya: Path | None) -> None:
    """Test that the found maya executable points to a file."""
    if maya is not None:
        assert maya.is_file()
    else:
        pytest.fail(reason="Maya was None")


@pytest.mark.skipif(
    os.environ.get("MAYA_VERSION") is None,
    reason="MAYA_VERSION not set",
)
def test_mayapy_is_file(mayapy: Path | None) -> None:
    """Test that the found mayapy executable points to a file."""
    if mayapy is not None:
        assert mayapy.is_file()
    else:
        pytest.fail(reason="Maya was None")
