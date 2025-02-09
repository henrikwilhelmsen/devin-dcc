# Copyright (C) 2025 Henrik Wilhelmsen.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at <https://mozilla.org/MPL/2.0/>.

"""Devin DCC blender CLI tests."""

import os
from collections.abc import Generator
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import ValidationError
from pydantic_settings import CliApp

from devin.cli.devin import (
    Devin,
)


@pytest.fixture(name="mock_call")
def fixture_mock_call() -> Generator[MagicMock | AsyncMock, None, None]:
    """Fixture that mocks the call function."""
    with patch("devin.cli.blender.call") as mock:
        yield mock


@pytest.fixture(name="mock_get_blender")
def fixture_mock_get_blender() -> Generator[MagicMock | AsyncMock, None, None]:
    """Fixture that mocks the Blender executable path."""
    with patch("devin.cli.blender.get_blender") as mock:
        mock.return_value = Path("usr/local/Blender Foundation/blender 4.3/blender")
        yield mock


def test_blender_no_args(
    mock_call: MagicMock | AsyncMock,
    mock_get_blender: MagicMock | AsyncMock,
    mock_env: os._Environ[str],
) -> None:
    """Test that the maya command runs with no arguments and calls the maya exe."""
    CliApp().run(Devin, cli_args=["blender"])
    mock_call.assert_called_once()
    _, kwargs = mock_call.call_args
    assert kwargs["args"][0] == mock_get_blender.return_value.as_posix()


def test_blender_args(
    mock_call: MagicMock | AsyncMock,
    mock_get_blender: MagicMock | AsyncMock,
    mock_env: os._Environ[str],
) -> None:
    """Test that the --args option passes values to the Blender exe as expected."""
    CliApp().run(
        Devin,
        # Note: Need to use a JSON style list or a single string "--args=-batch,..."
        # for the CLI to not confuse the -batch argument as a new option
        cli_args=["blender", "--args", "[-batch,--foo,bar]"],
    )

    mock_call.assert_called_once()
    _, kwargs = mock_call.call_args

    assert kwargs["args"] == [
        mock_get_blender.return_value.as_posix(),
        "-batch",
        "--foo",
        "bar",
    ]


# TODO: Move input and expected paths to fixtures
def test_blender_paths(
    mock_call: MagicMock | AsyncMock,
    mock_get_blender: MagicMock | AsyncMock,
    mock_env: os._Environ[str],
    tmp_path: Path,
) -> None:
    """Test that the various path options are passed to their matching env vars."""
    path_count = 10

    system_extensions = Path(tmp_path / "system_extensions")
    system_scripts = Path(tmp_path / "system_scripts")
    site_paths = [Path(tmp_path / f"python_{i}") for i in range(path_count)]

    for path in (system_extensions, system_scripts, *site_paths):
        path.mkdir()

    system_extensions_arg = ["--system-extensions", system_extensions.as_posix()]
    system_scripts_arg = ["--system-scripts", system_scripts.as_posix()]
    site_path_arg = [
        "--site-path",
        ",".join([x.as_posix() for x in site_paths]),
    ]

    # Run the cli
    CliApp().run(
        Devin,
        cli_args=[
            "blender",
            *site_path_arg,
            *system_extensions_arg,
            *system_scripts_arg,
        ],
    )

    mock_call.assert_called_once()
    _, kwargs = mock_call.call_args

    # Check that the paths passed to the command was added to env
    expected_site_path = ";".join([x.as_posix() for x in site_paths])

    assert system_extensions.as_posix() == kwargs["env"]["BLENDER_SYSTEM_EXTENSIONS"]
    assert system_scripts.as_posix() == kwargs["env"]["BLENDER_SYSTEM_SCRIPTS"]
    assert expected_site_path in kwargs["env"]["BLENDER_SITE_PATH"]


def test_blender_executable_arg(
    mock_call: MagicMock | AsyncMock,
    mock_env: os._Environ[str],
    tmp_path: Path,
) -> None:
    """Test the --executable argument gets passed as the first arg in the call."""
    executable = tmp_path / "blender"
    executable.touch()

    CliApp().run(
        Devin,
        cli_args=[
            "blender",
            "--executable",
            executable.as_posix(),
        ],
    )

    mock_call.assert_called_once()
    _, kwargs = mock_call.call_args

    assert kwargs["args"] == [executable.as_posix()]


def test_blender_invalid_version(mock_get_blender: MagicMock | AsyncMock) -> None:
    """Test that a ValidationError is raised if an invalid version is passed."""
    with pytest.raises(ValidationError):
        CliApp().run(Devin, cli_args=["blender", "-v", "invalid"])


def test_blender_missing_executable(mock_get_blender: MagicMock | AsyncMock) -> None:
    """Test that a FileNotFoundError is raised if the get_maya function returns None."""
    mock_get_blender.return_value = None

    with pytest.raises(FileNotFoundError):
        CliApp().run(Devin, cli_args=["blender"])
