# Copyright (C) 2025 Henrik Wilhelmsen.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You

"""Module for locating and managing Blender."""

import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def get_blender(version: str) -> Path:
    """Get the path to a Blender executable for the given version.

    Will download the requested version from blender.org if it's not found.

    Args:
        version: Which version of Blender to get. See `settings.BLENDER_VERSIONS` for
        supported versions.

    Raises:
        ValueError: If the given version is not supported.
    """
    if sys.platform == "win32":
        exe = Path(
            rf"C:\Program Files\Blender Foundation\Blender {version}\blender.exe",
        )

        if not exe.exists():
            logger.exception(
                "Unable to locate executable for Blender %s",
                version,
            )
            raise FileNotFoundError

        return exe

    logger.exception("Blender exe for current platform not implemented yet.")
    raise NotImplementedError

    # TODO: Download Blender
    # https://www.blender.org/download/release/Blender4.3/blender-4.3.2-windows-x64.zip/
