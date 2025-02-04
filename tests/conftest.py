# Copyright (C) 2025 Henrik Wilhelmsen.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at <https://mozilla.org/MPL/2.0/>.

"""Pytest test fixtures and utilities."""

import os
from collections.abc import Generator
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.fixture(name="mock_env")
def fixture_mock_env() -> Generator[os._Environ[str], None, None]:
    """Fixture that provides a clean environment."""
    with patch.dict(os.environ, {}, clear=True):
        yield os.environ


@pytest.fixture(name="mock_get_blender")
def fixture_mock_get_blender() -> Generator[MagicMock | AsyncMock, None, None]:
    """Fixture that mocks the Blender executable path."""
    with patch("devin.cli.get_blender") as mock:
        mock.return_value = Path(
            "C:/Program Files/Blender Foundation/Blender 4.0/blender.exe",
        )
        yield mock
