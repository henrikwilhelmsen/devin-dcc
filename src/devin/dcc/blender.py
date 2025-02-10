# Copyright (C) 2025 Henrik Wilhelmsen.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You

"""Module for locating and managing Blender."""

import logging
import platform
from contextlib import suppress
from pathlib import Path
from typing import Literal

from devin.constants import DEVIN_RESOURCE_DIR, PLATFORMS

logger = logging.getLogger(__name__)


# Supported Blender versions
BLENDER_VERSIONS = Literal["3.6", "4.2", "4.3"]

# Mapping of supported Blender Python versions
BLENDER_PYTHON_MAP = {"3.6": "3.10", "4.2": "3.11", "4.3": "3.11"}

# Download URLs for Blender versions
BLENDER_DOWNLOADS: dict[PLATFORMS, dict[BLENDER_VERSIONS, str]] = {
    "Linux": {
        "3.6": "https://download.blender.org/release/Blender3.6/blender-3.6.8-linux-x64.tar.xz",
        "4.2": "https://download.blender.org/release/Blender4.2/blender-4.2.6-linux-x64.tar.xz",
        "4.3": "https://download.blender.org/release/Blender4.3/blender-4.3.2-linux-x64.tar.xz",
    },
    "Windows": {
        "3.6": "https://download.blender.org/release/Blender3.6/blender-3.6.8-windows-x64.zip",
        "4.2": "https://download.blender.org/release/Blender4.2/blender-4.2.6-windows-x64.zip",
        "4.3": "https://download.blender.org/release/Blender4.3/blender-4.3.2-windows-x64.zip",
    },
}

DEVIN_BLENDER_DIR = DEVIN_RESOURCE_DIR / "blender"

# Path to the Blender executable relative to the downloaded Blender dir
BLENDER_EXE_LOCATION = "blender.exe" if platform.system == "Windows" else "blender"


def get_existing_downloads() -> list[Path]:
    """Get a list of directories in `DEVIN_BLENDER_DIR`."""
    return [x for x in DEVIN_BLENDER_DIR.glob("*") if x.is_dir()]


def get_existing_devin_blender(version: BLENDER_VERSIONS) -> Path | None:
    """Get the path to the an existing Blender exe downloaded by devin-dcc."""
    for directory in get_existing_downloads():
        versioned_dir_name = (
            Path(BLENDER_DOWNLOADS["Windows"][version]).stem
            if platform.system == "Windows"
            else Path(BLENDER_DOWNLOADS["Linux"][version]).stem
        )

        if versioned_dir_name == directory.name:
            blender = directory / BLENDER_EXE_LOCATION
            return blender if blender.is_file() else None

    return None


def download_blender(version: BLENDER_VERSIONS, target_dir: Path) -> Path:
    """Download and extract Blender to target dir, return path to downloaded dir."""
    raise NotImplementedError


def get_blender(version: BLENDER_VERSIONS) -> Path:
    """Get the path to a Blender executable for the given version if installed."""
    devin_blender = get_existing_devin_blender(version=version)
    if devin_blender is not None:
        return devin_blender

    if platform.system() == "Windows":
        default_blender = Path(
            rf"C:\Program Files\Blender Foundation\Blender {version}\blender.exe",
        )
        if default_blender.is_file():
            return default_blender

    msg = f"Failed to locate Blender '{version}'"
    logger.exception(msg=msg)
    raise FileNotFoundError(msg)


def get_blender_download_if_missing(version: BLENDER_VERSIONS) -> Path:
    """Get the path to blender, download the given version if not found."""
    with suppress(FileNotFoundError):
        return get_blender(version=version)

    # TODO: Add try/except
    blender_dir = download_blender(version=version, target_dir=DEVIN_BLENDER_DIR)
    blender = blender_dir / BLENDER_EXE_LOCATION

    if blender.is_file:
        return blender

    msg = (
        f"Failed to download Blender '{version}', could not locate executable in "
        f"downloaded directory '{blender_dir}'"
    )
    logger.exception(msg=msg)
    raise FileNotFoundError(msg)
