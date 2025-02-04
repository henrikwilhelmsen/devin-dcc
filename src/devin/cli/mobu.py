# Copyright (C) 2025 Henrik Wilhelmsen.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at <https://mozilla.org/MPL/2.0/>.

"""Devin DCC mobu and mobupy CLI commands."""

import logging
import os
import shutil
import sys
import tempfile
from functools import cached_property
from pathlib import Path
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
from pydantic_settings import (
    CliImplicitFlag,
)

from devin.cli.base import BaseCommand
from devin.constants import DATA_DIR
from devin.dcc.mobu import get_mobu, get_mobupy

logger = logging.getLogger(__name__)

# Supported Motionbuilder versions
MOBU_VERSIONS = Literal["2022", "2023", "2024", "2025"]

# Mapping of supported Motionbuilder Python versions
MOBU_PYTHON_MAP = {"2022": "3.7", "2023": "3.7", "2024": "3.10", "2025": "3.11"}


class MobuBase(BaseCommand):
    """Motionbuilder base command model."""

    include_prefix_site: CliImplicitFlag[bool] = Field(
        default=False,
        description="Add site-packages dir of current Python env to Mobu at launch",
    )
    version: MOBU_VERSIONS = Field(
        default="2025",
        validation_alias=AliasChoices("version", "v"),
    )
    args: list[str] = Field(
        default_factory=list,
        description="Additional arguments to pass to executable",
    )
    temp_config_dir: CliImplicitFlag[bool] = Field(
        default=False,
        description="Launch with MB_CONFIG_DIR set to an empty temp dir",
    )
    site_path: list[DirectoryPath] = Field(
        default_factory=list,
        description="Extra paths to add to executable's site directories at launch",
    )
    _executable_help = (
        "Optional path to the executable to use. If not set, "
        "the program will search the default install locations or "
        "the Windows registry for one."
    )
    executable: FilePath | None = Field(
        default=None,
        description=_executable_help,
        validation_alias=AliasChoices("executable", "e"),
    )

    @computed_field
    @property
    def _computed_site_path(self) -> str | None:
        site_dirs = []
        if self.include_prefix_site:
            site_dirs = [(Path(sys.prefix) / "Lib" / "site-packages")]

        if self.site_path:
            site_dirs.extend(self.site_path)

        if site_dirs:
            return ";".join([x.as_posix() for x in site_dirs])

        return None

    @field_validator("version", mode="after")
    @classmethod
    def check_python_version_matches_sys(cls, value: str, info: ValidationInfo) -> str:
        """Check that Python version of the requested Motionbuilder matches sys.version.

        Only runs if include_prefix_site is set to true, otherwise there's no reason
        the Python version needs to match.
        """
        mobu_py_req = MOBU_PYTHON_MAP.get(value)
        current_py = f"{sys.version_info.major}.{sys.version_info.minor}"

        if info.data["include_prefix_site"] and current_py != mobu_py_req:
            msg = (
                f"Mobu {value} requires Python {mobu_py_req}, "
                "unable to launch with the '--include-prefix-site' flag and "
                f"Python {current_py}. Either remove the flag or run this command "
                f"again with Python {mobu_py_req}"
            )
            raise ValueError(msg)

        return value


class Mobupy(MobuBase):
    """Launch mobupy."""

    @computed_field
    @cached_property
    def _computed_executable(self) -> FilePath:
        if self.executable is not None:
            return self.executable

        exe = get_mobupy(version=self.version)
        if exe is None:
            msg = (
                f"Could not locate Mobupy executable. Make sure Mobu {self.version} is "
                f"installed. If installed in a non-standard location, provide a path to"
                f" the Mobupy executable with the '--executable' option instead."
            )
            logger.exception(msg=msg)
            raise FileNotFoundError(msg)

        return exe

    @computed_field
    @cached_property
    def env(self) -> dict[str, str]:
        """Set up the mobupy environment."""
        env = {
            **os.environ.copy(),
            "PYTHONUNBUFFERED": "1",
            "PYDEVD_DISABLE_FILE_VALIDATION": "1",
        }
        # MOBU_SITE_PATH - extra site dirs (see mobu_scripts/startup/bootstrap.py)
        if self._computed_site_path is not None:
            env["MOTIONBUILDER_SITE_PATH"] = self._computed_site_path

        # Run bootstrap script when starting the mobupy interpreter
        env["PYTHONSTARTUP"] = (
            DATA_DIR / "mobu_scripts" / "startup" / "bootstrap.py"
        ).as_posix()

        return env

    def cli_cmd(self) -> None:
        """Mobupy CLI command.

        Launch mobupy with the resolved environment and arguments.
        """
        self.configure_logging()
        args = [self._computed_executable.as_posix(), *self.args]
        env = self.env

        # MB_CONFIG_DIR - user config, use to override and run with clean setup
        if self.temp_config_dir:
            temp_dir = tempfile.mkdtemp()
            env["MB_CONFIG_DIR"] = temp_dir
            logger.info("Created temp config dir: '%s'", temp_dir)

        try:
            call(
                args=args,
                env=env,
            )
        finally:
            if self.temp_config_dir:
                shutil.rmtree(temp_dir)
                logger.info("Deleted temp config dir: '%s'", temp_dir)


class Mobu(MobuBase):
    """Launch MotionBuilder."""

    plugin_path: list[DirectoryPath] = Field(
        default_factory=list,
        description="Extra paths to add to MOTIONBUILDER_PLUGIN_PATH",
    )
    module_path: list[DirectoryPath] = Field(
        default_factory=list,
        description="Extra paths to add to MOTIONBUILDER_MODULE_PATH",
    )
    python_startup: list[DirectoryPath] = Field(
        default_factory=list,
        description="Extra paths to add to MOTIONBUILDER_PYTHON_STARTUP",
    )

    @computed_field
    @cached_property
    def _computed_executable(self) -> FilePath:
        if self.executable is not None:
            return self.executable

        exe = get_mobu(version=self.version)
        if exe is None:
            msg = (
                f"Could not locate Mobu executable. Make sure Mobu {self.version} is "
                f"installed. If installed in a non-standard location, provide a path to"
                f" the Mobu executable with the '--executable' option instead."
            )

            logger.exception(msg=msg)
            raise FileNotFoundError(msg)

        return exe

    @computed_field
    @cached_property
    def env(self) -> dict[str, str]:
        """Set up the Motionbuilder environment."""
        env = {
            **os.environ.copy(),
            "PYTHONUNBUFFERED": "1",
            "PYDEVD_DISABLE_FILE_VALIDATION": "1",
        }

        # MOTIONBUILDER_PLUGIN_PATH - extra plugins (list)
        if self.plugin_path:
            env["MOTIONBUILDER_PLUGIN_PATH"] = ";".join(
                [x.as_posix() for x in self.plugin_path],
            )

        # MOTIONBUILDER_MODULE_PATH - extra modules (list)
        if self.module_path:
            env["MOTIONBUILDER_MODULE_PATH"] = ";".join(
                [x.as_posix() for x in self.module_path],
            )

        # MOTIONBUILDER_PYTHON_STARTUP - extra startup scripts (list)
        startup_dirs = [(DATA_DIR / "mobu_scripts" / "startup")]
        if self.python_startup:
            startup_dirs.extend(self.python_startup)

        env["MOTIONBUILDER_PYTHON_STARTUP"] = ";".join(
            [x.as_posix() for x in startup_dirs],
        )

        # MOBU_SITE_PATH - extra site dirs (see mobu_scripts/startup/bootstrap.py)
        if self._computed_site_path is not None:
            env["MOTIONBUILDER_SITE_PATH"] = self._computed_site_path

        return env

    def cli_cmd(self) -> None:
        """Mobu CLI command.

        Launch Motionbuilder with the resolved environment and arguments.
        """
        self.configure_logging()
        args = [self._computed_executable.as_posix(), *self.args]
        env = self.env

        # MB_CONFIG_DIR - user config, use to override and run with clean setup
        if self.temp_config_dir:
            temp_dir = tempfile.mkdtemp()
            env["MB_CONFIG_DIR"] = temp_dir
            logger.info("Created temp config dir: '%s'", temp_dir)

        try:
            call(
                args=args,
                env=env,
            )
        finally:
            if self.temp_config_dir:
                shutil.rmtree(temp_dir)
                logger.info("Deleted temp config dir: '%s'", temp_dir)
