# Copyright (C) 2025 Henrik Wilhelmsen.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at <https://mozilla.org/MPL/2.0/>.

"""Devin DCC blender CLI command."""

import logging
import os
from functools import cached_property
from subprocess import call
from typing import Literal

from pydantic import DirectoryPath, Field, computed_field

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

    version: Literal["3.6", "4.2", "4.3"]
    args: list[str] = Field(default_factory=list)
    site_dir: list[DirectoryPath] = Field(default_factory=list)
    system_extensions: DirectoryPath | None = Field(default=None)
    system_scripts: DirectoryPath | None = Field(default=None)
    download: bool = Field(default=True)

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

        # Add paths in `self.site_dir` to Blenders environment.
        # Variable is picked up and added with `site.sitepackages` in bootstrap script
        if self.site_dir:
            env["BLENDER_SITE_PATH"] = ";".join(
                [x.as_posix() for x in self.site_dir],
            )

        # Contains script to bootstrap Blender and reset variable to default
        env["BLENDER_USER_SCRIPTS"] = (DATA_DIR / "blender_scripts").as_posix()

        if self.system_scripts is not None:
            env["BLENDER_SYSTEM_SCRIPTS"] = self.system_scripts.as_posix()

        if self.system_extensions is not None:
            env["BLENDER_SYSTEM_EXTENSIONS"] = self.system_extensions.as_posix()

        return env

    def cli_cmd(self) -> None:
        """Blender CLI command.

        Launch Blender with the resolved environment and arguments.
        """
        self.configure_logging()
        args = [get_blender(version=self.version).as_posix()]

        # Easiest way to ensure addons are loaded only for current session
        if self.system_addons:
            args.extend(["--addons", ",".join(self.system_addons)])

        args.extend(self.args)

        call(
            args=args,
            env=self.env,
        )
