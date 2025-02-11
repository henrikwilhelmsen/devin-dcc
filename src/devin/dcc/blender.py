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
from shutil import unpack_archive
from typing import Literal

import httpx

from devin.constants import DEVIN_RESOURCE_DIR

logger = logging.getLogger(__name__)

# http success status code
SUCCESS_STATUS_CODE = 200

# Supported Blender versions
BLENDER_VERSIONS = Literal["3.6", "4.2", "4.3"]

# Mapping of supported Blender Python versions
BLENDER_PYTHON_MAP = {"3.6": "3.10", "4.2": "3.11", "4.3": "3.11"}

# Download URLs for Blender versions
BLENDER_DOWNLOADS: dict[str, dict[BLENDER_VERSIONS, str]] = {
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

ARCHIVE_FORMATS = {
    "Linux": "tar.xz",
    "Windows": "zip",
}

DEVIN_BLENDER_DIR = DEVIN_RESOURCE_DIR / "blender"

# Path to the Blender executable relative to the downloaded Blender dir
BLENDER_EXE_LOCATION = "blender.exe" if platform.system == "Windows" else "blender"


def get_devin_blender(version: BLENDER_VERSIONS) -> Path:
    """Get the path to the an existing Blender exe downloaded by devin-dcc."""
    for directory in [x for x in DEVIN_BLENDER_DIR.glob("*") if x.is_dir()]:
        if version in directory.name:
            blender = directory / BLENDER_EXE_LOCATION
            if blender.is_file():
                return blender

    msg = f"Unable to locate devin Blender for version {version}"
    raise FileNotFoundError(msg)


def download_blender(version: BLENDER_VERSIONS, target_dir: Path) -> None:
    """Download and extract Blender to the given target directory.

    Args:
        version (BLENDER_VERSIONS): The version of Blender to download.
        target_dir (Path): The directory to extract the downloaded archive to.

    Raises:
        NotImplementedError: If the platform is not supported.
        RuntimeError: If the download fails.
        OSError: If the archive cannot be extracted.
    """
    try:
        url = BLENDER_DOWNLOADS[platform.system()][version]
    except KeyError as e:
        msg = f"Failed to find url for Blender '{version}' on '{platform.system()}'"
        raise NotImplementedError(msg) from e

    logger.info("Downloading Blender %s from '%s'", version, url)
    response = httpx.get(url=url)
    if response.status_code != SUCCESS_STATUS_CODE:
        msg = f"Failed to download Blender '{version}' from '{url}'"
        raise RuntimeError(msg)

    archive = DEVIN_BLENDER_DIR / f"tmp.{ARCHIVE_FORMATS[platform.system()]}"
    dir_name = url.split("/")[-1].replace(f".{ARCHIVE_FORMATS[platform.system()]}", "")

    try:
        logger.info(
            "Extracting Blender %s to '%s'",
            version,
            DEVIN_BLENDER_DIR / dir_name,
        )
        if not archive.parent.exists():
            archive.parent.mkdir(parents=True)

        archive.touch()

        with archive.open(mode="wb") as file:
            file.write(response.content)

        unpack_archive(
            filename=archive,
            extract_dir=target_dir,
        )
    except OSError as e:
        msg = f"Failed to extract Blender archive '{archive}' to '{target_dir}'"
        raise OSError(msg) from e
    finally:
        archive.unlink(missing_ok=True)


def get_blender(version: BLENDER_VERSIONS) -> Path:
    """Get the path to a Blender executable for the given version if installed."""
    with suppress(FileNotFoundError):
        return get_devin_blender(version=version)

    if platform.system() == "Windows":
        default_blender = Path(
            rf"C:\Program Files\Blender Foundation\Blender {version}\blender.exe",
        )
        if default_blender.is_file():
            return default_blender

    msg = f"Failed to locate Blender '{version}'"
    raise FileNotFoundError(msg)


def get_blender_download_if_missing(version: BLENDER_VERSIONS) -> Path:
    """Get the path to a Blender executable for the given version.

    Args:
        version (BLENDER_VERSIONS): The version of Blender to get the executable for.

    Raises:
        FileNotFoundError: If the Blender executable cannot be found or downloaded.

    Returns:
        Path: Path to the Blender executable.
    """
    with suppress(FileNotFoundError):
        return get_blender(version=version)

    try:
        download_blender(version=version, target_dir=DEVIN_BLENDER_DIR)
    except (FileNotFoundError, OSError, NotImplementedError) as e:
        msg = f"Failed to download Blender {version}"
        raise FileNotFoundError(msg) from e

    with suppress(FileNotFoundError):
        return get_devin_blender(version=version)

    msg = (
        f"Failed to download Blender '{version}', could not locate executable in "
        f"'{DEVIN_BLENDER_DIR}' after extracting archive"
    )
    raise FileNotFoundError(msg)
