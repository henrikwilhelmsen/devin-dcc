# Copyright (C) 2025 Henrik Wilhelmsen.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at <https://mozilla.org/MPL/2.0/>.

"""Devin DCC maya and mayapy CLI tests."""

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
    with patch("devin.cli.maya.call") as mock:
        yield mock


@pytest.fixture(name="mock_get_maya")
def fixture_mock_get_maya() -> Generator[MagicMock | AsyncMock, None, None]:
    """Fixture that mocks the Maya executable path."""
    with patch("devin.cli.maya.get_maya") as mock:
        mock.return_value = Path("C:/Program Files/Autodesk/Maya2024/bin/maya.exe")
        yield mock


@pytest.fixture(name="mock_get_mayapy")
def fixture_mock_get_mayapy() -> Generator[MagicMock | AsyncMock, None, None]:
    """Fixture that mocks the MayaPy executable path."""
    with patch("devin.cli.maya.get_mayapy") as mock:
        mock.return_value = Path("C:/Program Files/Autodesk/Maya2024/bin/mayapy.exe")
        yield mock


def test_maya_no_args(
    mock_call: MagicMock | AsyncMock,
    mock_get_maya: MagicMock | AsyncMock,
    mock_env: os._Environ[str],
) -> None:
    """Test that the maya command runs with no arguments and calls the maya exe."""
    CliApp().run(Devin, cli_args=["maya"])
    mock_call.assert_called_once()
    _, kwargs = mock_call.call_args
    assert kwargs["args"] == [mock_get_maya.return_value.as_posix()]


def test_maya_args(
    mock_call: MagicMock | AsyncMock,
    mock_get_maya: MagicMock | AsyncMock,
    mock_env: os._Environ[str],
) -> None:
    """Test that the --args option passes values to the Maya executable as expected."""
    CliApp().run(
        Devin,
        # Note: Need to use a JSON style list or a single string "--args=-batch,..."
        # for the CLI to not confuse the -batch argument as a new option
        cli_args=["maya", "--args", "[-batch,--foo,bar]"],
    )

    mock_call.assert_called_once()
    _, kwargs = mock_call.call_args

    assert kwargs["args"] == [
        mock_get_maya.return_value.as_posix(),
        "-batch",
        "--foo",
        "bar",
    ]


# TODO: Move input and expected paths to fixtures
def test_maya_paths(
    mock_call: MagicMock | AsyncMock,
    mock_get_maya: MagicMock | AsyncMock,
    mock_env: os._Environ[str],
    tmp_path: Path,
) -> None:
    """Test that the various path options are passed to their matching env vars."""
    path_count = 10

    plugin_paths = [Path(tmp_path / f"plugins_{i}") for i in range(path_count)]
    module_paths = [Path(tmp_path / f"modules_{i}") for i in range(path_count)]
    python_paths = [Path(tmp_path / f"python_{i}") for i in range(path_count)]

    for path in [*plugin_paths, *module_paths, *python_paths]:
        path.mkdir()

    # Pydantic supports JSON, Argparse and lazy style lists
    # https://docs.pydantic.dev/latest/concepts/pydantic_settings/#lists

    # Argparse style with multiple --plugin-path passed
    plugin_args = [
        item for p in plugin_paths for item in ("--plugin-path", p.as_posix())
    ]

    # JSON style, with a comma-separated list within brackets []
    module_args = [
        "--module-path",
        f"[{','.join([x.as_posix() for x in module_paths])}]",
    ]

    # Lazy style, with a comma-separated list without the brackets
    python_args = [
        "--python-path",
        ",".join([x.as_posix() for x in python_paths]),
    ]

    # Run the cli
    CliApp().run(
        Devin,
        cli_args=[
            "maya",
            *plugin_args,
            *module_args,
            *python_args,
        ],
    )

    mock_call.assert_called_once()
    _, kwargs = mock_call.call_args

    # Check that the paths passed to the command was added to env
    expected_plugin_path = ";".join([x.as_posix() for x in plugin_paths])
    expected_module_path = ";".join([x.as_posix() for x in module_paths])
    expected_python_path = ";".join([x.as_posix() for x in python_paths])

    assert expected_plugin_path in kwargs["env"]["MAYA_PLUG_IN_PATH"]
    assert expected_module_path in kwargs["env"]["MAYA_MODULE_PATH"]
    assert expected_python_path in kwargs["env"]["PYTHONPATH"]


def test_maya_existing_python_path(
    mock_call: MagicMock | AsyncMock,
    mock_get_maya: MagicMock | AsyncMock,
    mock_env: os._Environ[str],
    tmp_path: Path,
) -> None:
    """Test that the --python-path argument respects existing PYTHONPATH values."""
    path_count = 10
    python_paths = [Path(tmp_path / f"python_{i}") for i in range(path_count)]

    for path in python_paths:
        path.mkdir()

    python_args = [
        "--python-path",
        ",".join([x.as_posix() for x in python_paths]),
    ]

    # Add pre-existing value to pythonpath to make sure it doesn't get removed
    existing_py_path = tmp_path / "existing" / "python" / "path"
    mock_env["PYTHONPATH"] = existing_py_path.as_posix()

    CliApp().run(
        Devin,
        cli_args=[
            "maya",
            *python_args,
        ],
    )

    mock_call.assert_called_once()
    _, kwargs = mock_call.call_args
    expected_python_path = ";".join([x.as_posix() for x in python_paths])

    assert expected_python_path in kwargs["env"]["PYTHONPATH"]
    assert existing_py_path.as_posix() in kwargs["env"]["PYTHONPATH"]


def test_maya_executable_arg(
    mock_call: MagicMock | AsyncMock,
    mock_env: os._Environ[str],
    tmp_path: Path,
) -> None:
    """Test the --executable argument gets passed as the first arg in the call."""
    executable = tmp_path / "maya.exe"
    executable.touch()

    CliApp().run(
        Devin,
        cli_args=[
            "maya",
            "--executable",
            executable.as_posix(),
        ],
    )

    mock_call.assert_called_once()
    _, kwargs = mock_call.call_args

    assert kwargs["args"] == [executable.as_posix()]


def test_maya_invalid_version(mock_get_maya: MagicMock | AsyncMock) -> None:
    """Test that a ValidationError is raised if an invalid version is passed."""
    with pytest.raises(ValidationError):
        CliApp().run(Devin, cli_args=["maya", "-v", "invalid"])


def test_maya_missing_executable(mock_get_maya: MagicMock | AsyncMock) -> None:
    """Test that a FileNotFoundError is raised if the get_maya function returns None."""
    mock_get_maya.return_value = None

    with pytest.raises(FileNotFoundError):
        CliApp().run(Devin, cli_args=["maya"])


def test_mayapy_no_args(
    mock_call: MagicMock | AsyncMock,
    mock_get_mayapy: MagicMock | AsyncMock,
    mock_env: os._Environ[str],
) -> None:
    """Test that the maya command runs with no arguments and calls the maya exe."""
    CliApp().run(Devin, cli_args=["mayapy"])
    mock_call.assert_called_once()
    _, kwargs = mock_call.call_args
    assert kwargs["args"][0] == mock_get_mayapy.return_value.as_posix()


def test_mayapy_args(
    mock_call: MagicMock | AsyncMock,
    mock_get_mayapy: MagicMock | AsyncMock,
    mock_env: os._Environ[str],
) -> None:
    """Test that the --args option passes values to the Maya executable as expected."""
    CliApp().run(
        Devin,
        # Note: Need to use a JSON style list or a single string "--args=-batch,..."
        # for the CLI to not confuse the -batch argument as a new option
        cli_args=["mayapy", "--args", "[-batch,--foo,bar]"],
    )

    mock_call.assert_called_once()
    _, kwargs = mock_call.call_args

    assert kwargs["args"] == [
        mock_get_mayapy.return_value.as_posix(),
        "-batch",
        "--foo",
        "bar",
    ]


def test_mayapy_executable_arg(
    mock_call: MagicMock | AsyncMock,
    mock_env: os._Environ[str],
    tmp_path: Path,
) -> None:
    """Test the --executable argument gets passed as the first arg in the call."""
    executable = tmp_path / "maya.exe"
    executable.touch()

    CliApp().run(
        Devin,
        cli_args=[
            "mayapy",
            "--executable",
            executable.as_posix(),
        ],
    )

    mock_call.assert_called_once()
    _, kwargs = mock_call.call_args

    assert kwargs["args"] == [executable.as_posix()]


def test_mayapy_missing_executable(mock_get_mayapy: MagicMock | AsyncMock) -> None:
    """Test that a FileNotFoundError is raised if the get_maya function returns None."""
    mock_get_mayapy.return_value = None

    with pytest.raises(FileNotFoundError):
        CliApp().run(Devin, cli_args=["mayapy"])
