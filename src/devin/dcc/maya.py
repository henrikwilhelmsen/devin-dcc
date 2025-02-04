# Copyright (C) 2025 Henrik Wilhelmsen.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You

"""Module for locating and managing Autodesk Maya."""

import logging
import os
import platform
from pathlib import Path

logger = logging.getLogger(__name__)


def _get_install_dir_linux(version: str) -> Path | None:
    """Get the Maya install directory on Linux systems."""
    maya_default_path = Path(f"/usr/autodesk/maya{version}")

    if maya_default_path.exists():
        return maya_default_path

    return None


def _get_maya_install_dir_windows(version: str) -> Path | None:
    """Get the Maya install path from the Windows registry."""
    if platform.system() == "Windows":
        from winreg import (
            HKEY_LOCAL_MACHINE,
            ConnectRegistry,
            OpenKey,
            QueryValueEx,
        )

        reg = ConnectRegistry(None, HKEY_LOCAL_MACHINE)
        try:
            reg_key = OpenKey(
                reg,
                f"SOFTWARE\\AUTODESK\\MAYA\\{version}\\Setup\\InstallPath",
            )
        except FileNotFoundError:
            logger.debug(
                "Unable to locate install path for Maya %s in registry",
                version,
            )
            return None

        maya_install_dir = Path(QueryValueEx(reg_key, "MAYA_INSTALL_LOCATION")[0])

        if maya_install_dir.exists():
            return maya_install_dir

    return None


def get_maya_install_dir(version: str) -> Path | None:
    """Get Maya install location on supported platforms (Linux and Windows)."""
    maya_location_var = os.environ.get("MAYA_LOCATION")

    if maya_location_var and version in maya_location_var:
        install_dir = Path(maya_location_var)

        if install_dir.exists():
            return install_dir

    if platform.system() == "Windows":
        return _get_maya_install_dir_windows(version=version)

    if platform.system() == "Linux":
        return _get_install_dir_linux(version=version)

    return None


def _get_exe(
    version: str,
    name_system_map: dict[str, str],
    default_name: str,
) -> Path | None:
    """Get the path to any executable in the bin directory of the given Maya version.

    Args:
        version: Maya version identifier.
        name_system_map: Mapping of platform.system() name to executable name.
        default_name: Default executable name if mapping system mapping fails.

    Returns:
        Path to the executable if it exists.
    """
    install_dir = get_maya_install_dir(version=version)
    if install_dir is None:
        return None

    exe_name = name_system_map.get(
        platform.system(),
        default_name,
    )
    exe = install_dir / "bin" / exe_name

    if exe.exists():
        return exe

    return None


def get_maya(version: str) -> Path | None:
    """Get the path to the maya executable."""
    name_map = {"Linux": "maya", "Windows": "maya.exe"}
    default_name = "maya"

    return _get_exe(
        version=version,
        name_system_map=name_map,
        default_name=default_name,
    )


def get_mayapy(version: str) -> Path | None:
    """Get the path to the mayapy executable."""
    name_map = {"Linux": "mayapy", "Windows": "mayapy.exe"}
    default_name = "mayapy"

    return _get_exe(
        version=version,
        name_system_map=name_map,
        default_name=default_name,
    )
