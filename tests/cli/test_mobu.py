# Copyright (C) 2025 Henrik Wilhelmsen.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at <https://mozilla.org/MPL/2.0/>.

"""Devin DCC mobu and mobupy CLI tests."""

import os
import sys
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
    with patch("devin.cli.mobu.call") as mock:
        yield mock


@pytest.fixture(name="mock_get_mobu")
def fixture_mock_get_mobu() -> Generator[MagicMock | AsyncMock, None, None]:
    """Fixture that mocks the MotionBuilder executable path."""
    with patch("devin.cli.mobu.get_mobu") as mock:
        mock.return_value = Path(
            "C:/Program Files/Autodesk/MotionBuilder2024/bin/motionbuilder.exe",
        )
        yield mock


@pytest.fixture(name="mock_get_mobupy")
def fixture_mock_get_mobupy() -> Generator[MagicMock | AsyncMock, None, None]:
    """Fixture that mocks the MotionBuilder Python executable path."""
    with patch("devin.cli.mobu.get_mobupy") as mock:
        mock.return_value = Path(
            "C:/Program Files/Autodesk/MotionBuilder2024/bin/mobupy.exe",
        )
        yield mock


def test_mobu_no_args(
    mock_call: MagicMock | AsyncMock,
    mock_get_mobu: MagicMock | AsyncMock,
    mock_env: os._Environ[str],
) -> None:
    """Test that the mobu command runs with no arguments and calls the mobu exe."""
    CliApp().run(Devin, cli_args=["mobu"])
    mock_call.assert_called_once()
    _, kwargs = mock_call.call_args
    assert kwargs["args"] == [mock_get_mobu.return_value.as_posix()]


def test_mobu_args(
    mock_call: MagicMock | AsyncMock,
    mock_get_mobu: MagicMock | AsyncMock,
    mock_env: os._Environ[str],
) -> None:
    """Test that the --args option passes values to the mobu executable as expected."""
    CliApp().run(
        Devin,
        # Note: Need to use a JSON style list or a single string "--args=-batch,..."
        # for the CLI to not confuse the -batch argument as a new option
        cli_args=["mobu", "--args", "[-batch,--foo,bar]"],
    )

    mock_call.assert_called_once()
    _, kwargs = mock_call.call_args

    assert kwargs["args"] == [
        mock_get_mobu.return_value.as_posix(),
        "-batch",
        "--foo",
        "bar",
    ]


def test_mobupy_no_args(
    mock_call: MagicMock | AsyncMock,
    mock_get_mobupy: MagicMock | AsyncMock,
    mock_env: os._Environ[str],
) -> None:
    """Test that the mobu command runs with no arguments and calls the mobu exe."""
    CliApp().run(Devin, cli_args=["mobupy"])
    mock_call.assert_called_once()
    _, kwargs = mock_call.call_args
    assert kwargs["args"] == [mock_get_mobupy.return_value.as_posix()]


def test_mobupy_args(
    mock_call: MagicMock | AsyncMock,
    mock_get_mobupy: MagicMock | AsyncMock,
    mock_env: os._Environ[str],
) -> None:
    """Test that the --args option passes values to the mobupy executable."""
    CliApp().run(
        Devin,
        # Note: Need to use a JSON style list or a single string "--args=-batch,..."
        # for the CLI to not confuse the -batch argument as a new option
        cli_args=["mobupy", "--args", "[-batch,--foo,bar]"],
    )

    mock_call.assert_called_once()
    _, kwargs = mock_call.call_args

    assert kwargs["args"] == [
        mock_get_mobupy.return_value.as_posix(),
        "-batch",
        "--foo",
        "bar",
    ]


# TODO: Move input and expected paths to fixtures
def test_mobu_paths(
    mock_call: MagicMock | AsyncMock,
    mock_get_mobu: MagicMock | AsyncMock,
    mock_env: os._Environ[str],
    tmp_path: Path,
) -> None:
    """Test that the various path options are passed to their matching env vars."""
    path_count = 10

    site_paths = [Path(tmp_path / f"site_{i}") for i in range(path_count)]
    plugin_paths = [Path(tmp_path / f"plugins_{i}") for i in range(path_count)]
    module_paths = [Path(tmp_path / f"modules_{i}") for i in range(path_count)]
    python_startup_paths = [Path(tmp_path / f"python_{i}") for i in range(path_count)]

    for path in [*plugin_paths, *module_paths, *site_paths, *python_startup_paths]:
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
    site_args = [
        "--site-path",
        ",".join([x.as_posix() for x in site_paths]),
    ]

    startup_args = [
        "--python-startup",
        ",".join([x.as_posix() for x in python_startup_paths]),
    ]

    # Run the cli
    CliApp().run(
        Devin,
        cli_args=[
            "mobu",
            *plugin_args,
            *module_args,
            *site_args,
            *startup_args,
        ],
    )

    mock_call.assert_called_once()
    _, kwargs = mock_call.call_args

    # Check that the paths passed to the command was added to env
    expected_plugin_path = os.pathsep.join([x.as_posix() for x in plugin_paths])
    expected_module_path = os.pathsep.join([x.as_posix() for x in module_paths])
    expected_site_path = os.pathsep.join([x.as_posix() for x in site_paths])
    expected_startup_path = os.pathsep.join(
        [x.as_posix() for x in python_startup_paths],
    )

    assert expected_plugin_path in kwargs["env"]["MOTIONBUILDER_PLUGIN_PATH"]
    assert expected_module_path in kwargs["env"]["MOTIONBUILDER_MODULE_PATH"]
    assert expected_site_path in kwargs["env"]["MOTIONBUILDER_SITE_PATH"]
    assert expected_startup_path in kwargs["env"]["MOTIONBUILDER_PYTHON_STARTUP"]


def test_mobu_executable_arg(
    mock_call: MagicMock | AsyncMock,
    mock_env: os._Environ[str],
    tmp_path: Path,
) -> None:
    """Test the --executable argument gets passed as the first arg in the call."""
    executable = tmp_path / "mobu.exe"
    executable.touch()

    CliApp().run(
        Devin,
        cli_args=[
            "mobu",
            "--executable",
            executable.as_posix(),
        ],
    )

    mock_call.assert_called_once()
    _, kwargs = mock_call.call_args

    assert kwargs["args"][0] == executable.as_posix()


def test_mobupy_executable_arg(
    mock_call: MagicMock | AsyncMock,
    mock_env: os._Environ[str],
    tmp_path: Path,
) -> None:
    """Test the --executable argument gets passed as the first arg in the call."""
    executable = tmp_path / "mobupy.exe"
    executable.touch()

    CliApp().run(
        Devin,
        cli_args=[
            "mobupy",
            "--executable",
            executable.as_posix(),
        ],
    )

    mock_call.assert_called_once()
    _, kwargs = mock_call.call_args

    assert kwargs["args"][0] == executable.as_posix()


def test_mobu_executable_arg_non_existing(
    mock_call: MagicMock | AsyncMock,
    mock_env: os._Environ[str],
    tmp_path: Path,
) -> None:
    """Test that a ValidationError is raised if a non-existing file is passed as exe."""
    executable = tmp_path / "mobu.exe"

    with pytest.raises(ValidationError):
        CliApp().run(
            Devin,
            cli_args=[
                "mobu",
                "--executable",
                executable.as_posix(),
            ],
        )


def test_mobupy_executable_arg_non_existing(
    mock_call: MagicMock | AsyncMock,
    mock_env: os._Environ[str],
    tmp_path: Path,
) -> None:
    """Test that a ValidationError is raised if a non-existing file is passed as exe."""
    executable = tmp_path / "mobupy.exe"

    with pytest.raises(ValidationError):
        CliApp().run(
            Devin,
            cli_args=[
                "mobupy",
                "--executable",
                executable.as_posix(),
            ],
        )


def test_mobu_invalid_version(mock_get_mobu: MagicMock | AsyncMock) -> None:
    """Test that a ValidationError is raised if an invalid version is passed."""
    with pytest.raises(ValidationError):
        CliApp().run(Devin, cli_args=["mobu", "-v", "invalid"])


def test_mobupy_invalid_version(mock_get_mobupy: MagicMock | AsyncMock) -> None:
    """Test that a ValidationError is raised if an invalid version is passed."""
    with pytest.raises(ValidationError):
        CliApp().run(Devin, cli_args=["mobupy", "-v", "invalid"])


def test_mobu_missing_executable(mock_get_mobu: MagicMock | AsyncMock) -> None:
    """Test that a FileNotFoundError is raised if the get_mobu returns None."""
    mock_get_mobu.return_value = None

    with pytest.raises(FileNotFoundError):
        CliApp().run(Devin, cli_args=["mobu"])


def test_mobupy_missing_executable(mock_get_mobupy: MagicMock | AsyncMock) -> None:
    """Test that a FileNotFoundError is raised if the get_mobupy returns None."""
    mock_get_mobupy.return_value = None

    with pytest.raises(FileNotFoundError):
        CliApp().run(Devin, cli_args=["mobupy"])


def test_mobu_with_temp_config(
    mock_call: MagicMock | AsyncMock,
    mock_get_mobu: MagicMock | AsyncMock,
    mock_env: os._Environ[str],
    tmp_path: Path,
) -> None:
    """Test that the --temp-config-dir option creates and uses a tmp config dir."""
    with patch("tempfile.mkdtemp") as mock_mkdtemp:
        mock_mkdtemp.return_value = str(tmp_path)
        CliApp().run(Devin, cli_args=["mobu", "--temp-config-dir"])

        _, kwargs = mock_call.call_args
        assert kwargs["env"]["MB_CONFIG_DIR"] == str(tmp_path)


def test_mobupy_with_temp_config(
    mock_call: MagicMock | AsyncMock,
    mock_get_mobupy: MagicMock | AsyncMock,
    mock_env: os._Environ[str],
    tmp_path: Path,
) -> None:
    """Test that the --temp-config-dir option creates and uses a tmp config dir."""
    with patch("tempfile.mkdtemp") as mock_mkdtemp:
        mock_mkdtemp.return_value = str(tmp_path)
        CliApp().run(Devin, cli_args=["mobupy", "--temp-config-dir"])

        _, kwargs = mock_call.call_args
        assert kwargs["env"]["MB_CONFIG_DIR"] == str(tmp_path)


def test_mobu_with_prefix_site(
    mock_call: MagicMock | AsyncMock,
    mock_get_mobu: MagicMock | AsyncMock,
    mock_env: os._Environ[str],
    tmp_path: Path,
) -> None:
    """Test that the --include-prefix-site option adds prefix site to env var."""
    expected = (Path(sys.prefix) / "Lib" / "site-packages").as_posix()
    CliApp().run(Devin, cli_args=["mobu", "--include-prefix-site"])

    _, kwargs = mock_call.call_args
    result = kwargs["env"]["MOTIONBUILDER_SITE_PATH"]

    assert expected in result


def test_mobupy_with_prefix_site(
    mock_call: MagicMock | AsyncMock,
    mock_get_mobupy: MagicMock | AsyncMock,
    mock_env: os._Environ[str],
    tmp_path: Path,
) -> None:
    """Test that the --include-prefix-site option adds prefix site to env var."""
    expected = (Path(sys.prefix) / "Lib" / "site-packages").as_posix()
    CliApp().run(Devin, cli_args=["mobupy", "--include-prefix-site"])

    _, kwargs = mock_call.call_args
    result = kwargs["env"]["MOTIONBUILDER_SITE_PATH"]

    assert expected in result
