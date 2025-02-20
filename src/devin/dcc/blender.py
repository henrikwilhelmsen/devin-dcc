# Copyright (C) 2025 Henrik Wilhelmsen.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You

"""Module for locating and managing Blender."""

import logging
import platform
from logging import Logger
from pathlib import Path
from shutil import unpack_archive
from typing import Literal, TypeAlias

import httpx
from pydantic import BaseModel, computed_field

from devin.constants import DEVIN_RESOURCE_DIR

logger: Logger = logging.getLogger(__name__)

# http success status code
SUCCESS_STATUS_CODE = 200

# Supported Blender versions
BLENDER_VERSIONS: TypeAlias = Literal["3.6", "4.2", "4.3"]

# Mapping of supported Blender Python versions
BLENDER_PYTHON_MAP: dict[str, str] = {"3.6": "3.10", "4.2": "3.11", "4.3": "3.11"}

ARCHIVE_FORMATS: dict[str, str] = {
    "Linux": ".tar.xz",
    "Windows": ".zip",
}

DEVIN_BLENDER_DIR: Path = DEVIN_RESOURCE_DIR / "blender"

# Path to the Blender executable relative to the downloaded Blender dir
BLENDER_EXE_NAME: Literal["blender.exe", "blender"] = (
    "blender.exe" if platform.system() == "Windows" else "blender"
)


class BlenderDownloadConfig(BaseModel):
    """BaseModel to hold Blender download settings."""

    platform: Literal["Linux", "Windows"]
    version: BLENDER_VERSIONS
    long_version: str
    url: str

    @computed_field
    @property
    def python_version(self) -> str:
        """The Python version that ships with the Blender version of this config."""
        return BLENDER_PYTHON_MAP[self.version]

    @computed_field
    @property
    def archive_format(self) -> str:
        """The platform specific format of the archive to download from Blender."""
        return ARCHIVE_FORMATS[self.platform]

    @computed_field
    @property
    def dir_name(self) -> str:
        """The name of the install directory.

        Matches the name of the archive that was downloaded from Blender's servers.
        """
        return self.url.split("/")[-1].replace(self.archive_format, "")

    @computed_field
    @property
    def install_dir(self) -> Path:
        """The full path to the install directory."""
        return DEVIN_BLENDER_DIR / self.dir_name

    @computed_field
    @property
    def blender_exe(self) -> Path:
        """The full path to the downloaded Blender's executable."""
        return self.install_dir / BLENDER_EXE_NAME


BLENDER_DOWNLOAD_CONFIGS: list[BlenderDownloadConfig] = [
    BlenderDownloadConfig(
        platform="Linux",
        version="3.6",
        long_version="3.6.8",
        url="https://download.blender.org/release/Blender3.6/blender-3.6.8-linux-x64.tar.xz",
    ),
    BlenderDownloadConfig(
        platform="Windows",
        version="3.6",
        long_version="3.6.8",
        url="https://download.blender.org/release/Blender3.6/blender-3.6.8-windows-x64.zip",
    ),
    BlenderDownloadConfig(
        platform="Linux",
        version="4.2",
        long_version="4.2.6",
        url="https://download.blender.org/release/Blender4.2/blender-4.2.6-linux-x64.tar.xz",
    ),
    BlenderDownloadConfig(
        platform="Windows",
        version="4.2",
        long_version="4.2.6",
        url="https://download.blender.org/release/Blender4.2/blender-4.2.6-windows-x64.zip",
    ),
    BlenderDownloadConfig(
        platform="Linux",
        version="4.3",
        long_version="4.3.2",
        url="https://download.blender.org/release/Blender4.3/blender-4.3.2-linux-x64.tar.xz",
    ),
    BlenderDownloadConfig(
        platform="Windows",
        version="4.3",
        long_version="4.3.2",
        url="https://download.blender.org/release/Blender4.3/blender-4.3.2-windows-x64.zip",
    ),
]


def get_blender_download_config(version: BLENDER_VERSIONS) -> BlenderDownloadConfig:
    """Get the download config for the given Blender version.

    Args:
        version (BLENDER_VERSIONS): The version of Blender to get the config for.

    Raises:
        KeyError: If a config for the given version was not found.

    Returns:
        BlenderDownloadConfig: A BlenderDownloadConfig model for the given version.
    """
    system: str = platform.system()
    try:
        return next(
            x
            for x in BLENDER_DOWNLOAD_CONFIGS
            if x.version == version and x.platform == system
        )
    except StopIteration as e:
        msg: str = "Failed to find Blender download config"
        logger.exception(
            msg=msg,
            extra={"version": version, "system": system},
        )
        raise KeyError(msg) from e


def get_devin_blender(version: BLENDER_VERSIONS) -> Path | None:
    """Get the path to a Blender executable managed by devin-dcc.

    Args:
        version (BLENDER_VERSIONS): Version of Blender to get the executable for.

    Raises:
        KeyError: If unable to find a download config for the given version.

    Returns:
        Path | None: Path to the Blender executable if found, otherwise None.
    """
    try:
        config: BlenderDownloadConfig = get_blender_download_config(version=version)
    except KeyError as e:
        msg: str = "Failed to get Blender config, unable to search for existing install"
        logger.exception(msg, extra={"version": version})
        raise KeyError(msg) from e

    if config.blender_exe.is_file():
        return config.blender_exe

    return None


def download_blender(version: BLENDER_VERSIONS) -> Path:
    """Download the given version of Blender and return the path to the executable.

    The files will be downloaded to a version specific folder in the devin-dcc
    resources directory.

    Args:
        version (BLENDER_VERSIONS): The version of Blender to download.

    Raises:
        KeyError: If unable to find a download config for the given version.
        RuntimeError: If the download failed.
        OSError: If the archive extraction failed.
        FileNotFoundError: If the executable is not found after downloading.

    Returns:
        Path: The path to the downloaded Blender's executable.
    """
    try:
        download_config: BlenderDownloadConfig = get_blender_download_config(
            version=version,
        )
    except KeyError as e:
        msg: str = "Failed to get Blender config, unable to download"
        logger.exception(msg, extra={"version": version})
        raise KeyError(msg) from e

    logger.info(
        "Downloading Blender %s",
        version,
        extra={"version": version, "url": download_config.url},
    )

    response = httpx.get(url=download_config.url)
    if not response.is_success:
        msg = "Failed to download Blender"
        logger.exception(
            msg=msg,
            extra={
                version: version,
                "url": download_config.url,
                "status code": response.status_code,
                "reason": response.reason_phrase,
            },
        )
        raise RuntimeError(msg)

    tmp_archive = DEVIN_BLENDER_DIR / f"tmp{download_config.archive_format}"
    try:
        if not tmp_archive.parent.exists():
            tmp_archive.parent.mkdir(parents=True)

        tmp_archive.touch()

        with tmp_archive.open(mode="wb") as file:
            _ = file.write(response.content)

        unpack_archive(
            filename=tmp_archive,
            extract_dir=DEVIN_BLENDER_DIR,
        )
    except OSError as e:
        msg = "Failed to extract Blender archive"
        logger.exception(
            msg=msg,
            extra={"archive": tmp_archive, "target dir": download_config.install_dir},
        )
        raise OSError(msg) from e
    finally:
        tmp_archive.unlink(missing_ok=True)

    if download_config.blender_exe.is_file():
        logger.info(
            msg="Blender download successful",
            extra={"exe": download_config.blender_exe},
        )
        return download_config.blender_exe

    msg = "Failed to locate executable after download"
    logger.error(msg=msg, extra={"executable": download_config.blender_exe})
    raise FileNotFoundError(msg)


def get_blender(version: BLENDER_VERSIONS) -> Path | None:
    """Get the path to the Blender executable if it exists.

    Will check the devin-dcc resource dir for any downloads first, and then default
    system paths.

    Args:
        version (BLENDER_VERSIONS): The version of Blender to get the executable for.

    Raises:
        KeyError: If a KeyError occurred when searching for existing devin-dcc Blender.

    Returns:
        Path | None: The path to the Blender executable if found, otherwise None.
    """
    devin_blender: Path | None = None
    try:
        devin_blender = get_devin_blender(version=version)
    except KeyError as e:
        msg = "Encountered an error when searching for devin-dcc Blender install"
        logger.exception(
            msg=msg,
            extra={version: version},
        )
        raise KeyError(msg) from e

    if devin_blender is not None and devin_blender.is_file():
        return devin_blender

    if platform.system() == "Windows":
        default_blender = Path(
            rf"C:\Program Files\Blender Foundation\Blender {version}\blender.exe",
        )
        if default_blender.is_file():
            return default_blender

    return None


def get_blender_download_if_missing(version: BLENDER_VERSIONS) -> Path:
    """Get the path to a Blender executable for the given version.

    Args:
        version (BLENDER_VERSIONS): The version of Blender to get the executable for.

    Raises:
        FileNotFoundError: If the Blender executable cannot be found or downloaded.

    Returns:
        Path: Path to the Blender executable.
    """
    existing_blender = get_blender(version=version)
    if existing_blender is not None:
        return existing_blender

    try:
        return download_blender(version=version)
    except (FileNotFoundError, OSError, RuntimeError, KeyError) as e:
        msg = "Failed to download Blender"
        logger.exception(msg=msg, extra={"version": version})
        raise FileNotFoundError(msg) from e
