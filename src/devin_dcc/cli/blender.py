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
from typing import TYPE_CHECKING, Literal, TypeAlias

from dccpath import get_blender
from pydantic import (
    AliasChoices,
    DirectoryPath,
    Field,
    FilePath,
    ValidationInfo,
    computed_field,
    field_validator,
)

from devin_dcc.cli.base import BaseDCCCommand
from devin_dcc.constants import DATA_DIR

if TYPE_CHECKING:
    from pathlib import Path

logger = logging.getLogger(__name__)

# Supported Blender versions
BLENDER_VERSIONS: TypeAlias = Literal["3.6", "4.2", "4.3", "4.4"]

# Mapping of supported Blender Python versions
BLENDER_PYTHON_MAP: dict[BLENDER_VERSIONS, str] = {
    "3.6": "3.10",
    "4.2": "3.11",
    "4.3": "3.11",
    "4.4": "3.11",
}


class Blender(BaseDCCCommand):
    """Run Blender."""

    version: BLENDER_VERSIONS = Field(
        default="4.4",
        validation_alias=AliasChoices("version", "v"),
        description="Which version of Blender to run.",
    )
    system_extensions: DirectoryPath | None = Field(
        default=None,
        description="Path to the Blender SYSTEM_EXTENSIONS directory.",
    )
    system_scripts: DirectoryPath | None = Field(
        default=None,
        description="Path to the Blender SYSTEM_SCRIPTS directory.",
    )

    @field_validator("version", mode="after")
    @classmethod
    def check_python_version_matches_sys(
        cls,
        value: BLENDER_VERSIONS,
        info: ValidationInfo,
    ) -> str:
        """Check that Python version of the requested Blender matches sys.version.

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
            logger.error(msg)
            raise ValueError(msg)

        return value

    @computed_field
    @cached_property
    def system_addons(self) -> list[str]:
        """Get a list of addons from the SYSTEM_EXTENSIONS and _SCRIPTS directories."""
        addons: list[str] = []
        legacy_addons_dir: Path | None = (
            self.system_scripts / "addons" if self.system_scripts is not None else None
        )
        extension_addons_dir: Path | None = (
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
        env: dict[str, str] = {
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
        """Get the final executable path to run Blender with."""
        # If executable argument is provided, return it
        if self.executable is not None:
            logger.debug("Using provided executable: '%s'", self.executable)
            return self.executable

        try:
            blender = get_blender(version=self.version)
        except FileNotFoundError as e:
            msg = (
                f"Could not locate Blender executable. Make sure Blender {self.version}"
                " is installed. If installed in a non-standard location, provide a "
                "path to the Blender executable with the '--executable' option "
                "instead."
            )
            logger.exception(msg=msg)
            raise FileNotFoundError(msg) from e

        return blender

    def cli_cmd(self) -> None:
        """Blender CLI command.

        Launch Blender with the resolved environment and arguments.
        """
        self.configure_logging()
        args: list[str] = [self._computed_executable.as_posix(), *self.args]

        # Easiest way to ensure addons are loaded only for current session
        if self.system_addons:
            args.extend(["--addons", ",".join(self.system_addons)])

        _ = call(
            args=args,
            env=self.env,
        )
