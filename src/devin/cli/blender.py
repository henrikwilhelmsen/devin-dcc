# Copyright (C) 2025 Henrik Wilhelmsen.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at <https://mozilla.org/MPL/2.0/>.

"""Devin DCC blender CLI command."""

import logging
import os
import sys
from functools import cached_property
from subprocess import call
from typing import Literal

from pydantic import (
    AliasChoices,
    DirectoryPath,
    Field,
    FilePath,
    ValidationInfo,
    computed_field,
    field_validator,
)

from devin.cli.base import BaseCommand
from devin.constants import DATA_DIR
from devin.dcc.blender import get_blender

logger = logging.getLogger(__name__)


# Supported Blender versions
BLENDER_VERSIONS = Literal["3.6", "4.2", "4.3"]

# Mapping of supported Blender Python versions
BLENDER_PYTHON_MAP = {"3.6": "3.10", "4.2": "3.11", "4.3": "3.11"}


class Blender(BaseCommand):
    """Run Blender."""

    version: BLENDER_VERSIONS = Field(
        default="4.2",
        validation_alias=AliasChoices("version", "v"),
    )
    system_extensions: DirectoryPath | None = Field(default=None)
    system_scripts: DirectoryPath | None = Field(default=None)
    download: bool = Field(default=True)

    @field_validator("version", mode="after")
    @classmethod
    def check_python_version_matches_sys(cls, value: str, info: ValidationInfo) -> str:
        """Check that Python version of the requested Motionbuilder matches sys.version.

        Only runs if include_prefix_site is set to true, otherwise there's no reason
        the Python version needs to match.
        """
        blender_py_req = BLENDER_PYTHON_MAP.get(value)
        current_py = f"{sys.version_info.major}.{sys.version_info.minor}"

        if info.data["include_prefix_site"] and current_py != blender_py_req:
            msg = (
                f"Blender {value} requires Python {blender_py_req}, "
                "unable to launch with the '--include-prefix-site' flag and "
                f"Python {current_py}. Either remove the flag or run this command "
                f"again with Python {blender_py_req}"
            )
            raise ValueError(msg)

        return value

    @computed_field
    @cached_property
    def system_addons(self) -> list[str]:
        """Get a list of addons from the SYSTEM_EXTENSIONS and _SCRIPTS directories."""
        addons = []
        legacy_addons_dir = (
            self.system_scripts / "addons" if self.system_scripts is not None else None
        )
        extension_addons_dir = (
            self.system_extensions / "system"
            if self.system_extensions is not None
            else None
        )

        if legacy_addons_dir is not None:
            addons.extend([x.name for x in legacy_addons_dir.glob("*") if x.is_dir()])

        if extension_addons_dir is not None:
            # Blender recognizes new extension addons by adding 'bl_ext.system' to name
            addons.extend(
                [
                    f"bl_ext.system.{x.name}"
                    for x in extension_addons_dir.glob("*")
                    if x.is_dir()
                ],
            )

        return addons

    @computed_field
    @cached_property
    def env(self) -> dict[str, str]:
        """Set up the Blender environment."""
        env = {
            **os.environ.copy(),
            "PYTHONUNBUFFERED": "1",
            "PYDEVD_DISABLE_FILE_VALIDATION": "1",
        }

        # Add paths in `self.site_path` to Blenders environment.
        # Variable is picked up and added with `site.sitepackages` in bootstrap script
        if self._computed_site_path is not None:
            env["BLENDER_SITE_PATH"] = self._computed_site_path

        # Contains script to bootstrap Blender and reset variable to default
        env["BLENDER_USER_SCRIPTS"] = (DATA_DIR / "blender_scripts").as_posix()
        if self.system_scripts is not None:
            env["BLENDER_SYSTEM_SCRIPTS"] = self.system_scripts.as_posix()
        if self.system_extensions is not None:
            env["BLENDER_SYSTEM_EXTENSIONS"] = self.system_extensions.as_posix()

        return env

    @computed_field
    @cached_property
    def _computed_executable(self) -> FilePath:
        if self.executable is not None:
            return self.executable

        exe = get_blender(version=self.version)
        if exe is None:
            msg = (
                f"Could not locate Blender executable. Make sure Blender {self.version}"
                " is installed. If installed in a non-standard location, provide a "
                "path to the Blender executable with the '--executable' option "
                "instead."
            )
            logger.exception(msg=msg)
            raise FileNotFoundError(msg)

        return exe

    def cli_cmd(self) -> None:
        """Blender CLI command.

        Launch Blender with the resolved environment and arguments.
        """
        self.configure_logging()
        args = [self._computed_executable.as_posix(), *self.args]

        # Easiest way to ensure addons are loaded only for current session
        if self.system_addons:
            args.extend(["--addons", ",".join(self.system_addons)])

        call(
            args=args,
            env=self.env,
        )
