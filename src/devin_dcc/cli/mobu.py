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
from subprocess import call
from typing import Literal

from dccpath import get_mobu, get_mobupy
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

logger = logging.getLogger(__name__)

# Supported Motionbuilder versions
MOBU_VERSIONS = Literal["2022", "2023", "2024", "2025"]

# Mapping of supported Motionbuilder Python versions
MOBU_PYTHON_MAP = {"2022": "3.7", "2023": "3.7", "2024": "3.10", "2025": "3.11"}


class MobuBase(BaseDCCCommand):
    """Motionbuilder base command model."""

    version: MOBU_VERSIONS = Field(
        default="2025",
        validation_alias=AliasChoices("version", "v"),
    )

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

        try:
            return get_mobupy(version=self.version)
        except FileNotFoundError as e:
            msg = (
                f"Could not locate Mobupy executable. Make sure Mobu {self.version} is "
                f"installed. If installed in a non-standard location, provide a path to"
                f" the Mobupy executable with the '--executable' option instead."
            )
            logger.exception(msg=msg)
            raise FileNotFoundError(msg) from e

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
        temp_dir = None

        # MB_CONFIG_DIR - user config, use to override and run with clean setup
        if self.temp_config_dir:
            temp_dir = tempfile.mkdtemp()
            env["MB_CONFIG_DIR"] = temp_dir
            logger.info("Created temp config dir: '%s'", temp_dir)
        try:
            _ = call(
                args=args,
                env=env,
            )
        finally:
            if temp_dir is not None:
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

        try:
            return get_mobu(version=self.version)
        except FileNotFoundError as e:
            msg = (
                f"Could not locate Mobu executable. Make sure Mobu {self.version} is "
                f"installed. If installed in a non-standard location, provide a path to"
                f" the Mobu executable with the '--executable' option instead."
            )
            logger.exception(msg=msg)
            raise FileNotFoundError(msg) from e

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
            env["MOTIONBUILDER_PLUGIN_PATH"] = os.pathsep.join(
                [x.as_posix() for x in self.plugin_path],
            )

        # MOTIONBUILDER_MODULE_PATH - extra modules (list)
        if self.module_path:
            env["MOTIONBUILDER_MODULE_PATH"] = os.pathsep.join(
                [x.as_posix() for x in self.module_path],
            )

        # MOTIONBUILDER_PYTHON_STARTUP - extra startup scripts (list)
        startup_dirs = [(DATA_DIR / "mobu_scripts" / "startup")]
        if self.python_startup:
            startup_dirs.extend(self.python_startup)

        env["MOTIONBUILDER_PYTHON_STARTUP"] = os.pathsep.join(
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
        temp_dir = None

        # MB_CONFIG_DIR - user config, use to override and run with clean setup
        if self.temp_config_dir:
            temp_dir = tempfile.mkdtemp()
            env["MB_CONFIG_DIR"] = temp_dir
            logger.info("Created temp config dir: '%s'", temp_dir)

        try:
            _ = call(
                args=args,
                env=env,
            )
        finally:
            if temp_dir is not None:
                shutil.rmtree(temp_dir)
                logger.info("Deleted temp config dir: '%s'", temp_dir)
