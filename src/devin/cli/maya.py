# Copyright (C) 2025 Henrik Wilhelmsen.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at <https://mozilla.org/MPL/2.0/>.

"""Devin DCC maya and mayapy CLI commands."""

import logging
import os
import sys
from distutils.sysconfig import get_python_lib
from functools import cached_property
from pathlib import Path
from subprocess import call, check_output
from typing import Literal

from pydantic import (
    AliasChoices,
    DirectoryPath,
    Field,
    FilePath,
    computed_field,
)
from pydantic_settings import CliImplicitFlag

from devin.cli.base import BaseDCCCommand
from devin.constants import DATA_DIR
from devin.dcc.maya import get_maya, get_mayapy

logger = logging.getLogger(__name__)


# Supported Maya versions
MAYA_VERSIONS = Literal["2022", "2023", "2024", "2025"]

# Mapping of supported Maya Python versions
MAYA_PYTHON_MAP = {"2022": "3.7", "2023": "3.9", "2024": "3.10", "2025": "3.11"}


# TODO: Add --temp-config-dir option (see Mobu implementation)
class MayaBaseCommand(BaseDCCCommand):
    """Maya base command with fields that are shared between all Maya commands."""

    version: MAYA_VERSIONS = Field(
        default="2025",
        validation_alias=AliasChoices("version", "v"),
    )
    args: list[str] = Field(
        default_factory=list,
        description="Additional arguments to pass to executable",
    )
    python_path: list[DirectoryPath] = Field(
        default_factory=list,
        description="Extra paths to add to PYTHONPATH",
    )
    plugin_path: list[DirectoryPath] = Field(
        default_factory=list,
        description="Extra paths to add to MAYA_PLUG_IN_PATH",
    )
    module_path: list[DirectoryPath] = Field(
        default_factory=list,
        description="Extra paths to add to MAYA_MODULE_PATH",
    )

    @computed_field
    @cached_property
    def env(self) -> dict[str, str]:
        """Get the environment to run Maya with."""
        env = {
            **os.environ.copy(),
            "PYTHONUNBUFFERED": "1",
            "PYDEVD_DISABLE_FILE_VALIDATION": "1",
        }

        # Set up Maya plugin path
        if self.plugin_path:
            env["MAYA_PLUG_IN_PATH"] = ";".join(
                [x.as_posix() for x in self.plugin_path],
            )

        # Set up Maya module path
        if self.module_path:
            env["MAYA_MODULE_PATH"] = ";".join([x.as_posix() for x in self.module_path])

        self.python_path.append(DATA_DIR / "maya_scripts" / "startup")

        # Set up PYTHONPATH, prepending all paths provided as arguments
        if self.python_path:
            orig_python_path = env.get("PYTHONPATH")
            python_paths = [x.as_posix() for x in self.python_path]

            if orig_python_path is not None:
                python_paths.append(orig_python_path)

            env["PYTHONPATH"] = ";".join(python_paths)

        # MAYA_SITE_PATH - extra site dirs (see maya_scripts/userSetup.py)
        if self._computed_site_path is not None:
            env["MAYA_SITE_PATH"] = self._computed_site_path

        return env


class Maya(MayaBaseCommand):
    """Run Maya."""

    executable: FilePath | None = Field(
        default=None,
        validation_alias=AliasChoices("executable", "exe"),
        description="Path to Maya executable",
    )

    @computed_field
    @cached_property
    def _computed_executable(self) -> FilePath:
        if self.executable is not None:
            return self.executable

        exe = get_maya(version=self.version)
        if exe is None:
            msg = (
                f"Could not locate Maya {self.version} executable. Make sure it is "
                f"installed. If installed in a non-standard location, provide a path to"
                f" the Maya executable with the '--executable' option instead."
            )
            logger.exception(msg=msg)
            raise FileNotFoundError(msg)

        return exe

    def cli_cmd(self) -> None:
        """Run Maya with computed arguments and env."""
        self.configure_logging()
        args = [self._computed_executable.as_posix(), *self.args]
        _ = call(
            args=args,
            env=self.env,
        )


class Mayapy(MayaBaseCommand):
    """Run mayapy."""

    executable: FilePath | None = Field(
        default=None,
        validation_alias=AliasChoices("executable", "exe"),
        description="Path to mayapy executable",
    )

    create_prefix_sitecustomize: CliImplicitFlag[bool] = Field(
        default=False,
        description=(
            "Create a sitecustomize.py file pointing "
            "to mayapy's site packages dir in prefix site-packages and exit."
        ),
    )

    def create_sitecustomize(self) -> None:
        """Create a sitecustomize.py file in prefix site-packages dir."""
        # get site-packages from mayapy
        args = [
            self._computed_executable.as_posix(),
            "-c",
            "from site import getsitepackages;[print(x) for x in getsitepackages()]",
        ]
        sitepackages = [
            Path(x) for x in check_output(args=args, encoding="utf-8").splitlines()
        ]

        # get ngSkinTools from ApplicationPlugins dir
        ng_skin_tools_paths = [
            Path.home() / "Autodesk/ApplicationPlugins/ngskintools2",
            Path("/usr/autodesk/ApplicationPlugins/ngskintools2"),
            Path(os.getenv("PROGRAMDATA", default=""))
            / "Autodesk/ApplicationPlugins/ngskintools2",
        ]

        # Add the first ngSkinTools plugin dir that exists to sitepackages
        for p in ng_skin_tools_paths:
            if p.is_dir():
                sitepackages.append(p)
                break

        # Create the sitecustomize.py file
        sitecustomize_data = "\n".join(
            [
                "import site",
                *[f"site.addsitedir('{x.as_posix()}')" for x in sitepackages],
            ],
        )

        sitecustomize = Path(get_python_lib(prefix=sys.prefix)) / "sitecustomize.py"
        if not sitecustomize.is_file():
            sitecustomize.touch()

        _ = sitecustomize.write_text(data=sitecustomize_data)

        # Log the result
        msg = (
            f"wrote the following to file \n'{sitecustomize}':"
            f"\n\n{sitecustomize_data}\n"
        )
        logger.info(msg)

    @computed_field
    @cached_property
    def _computed_executable(self) -> FilePath:
        if self.executable is not None:
            return self.executable

        exe = get_mayapy(version=self.version)
        if exe is None:
            msg = (
                f"Could not locate mayapy executable. Make sure Maya {self.version} is "
                f"installed. If installed in a non-standard location, provide a path to"
                f" the mayapy executable with the '--executable' option instead."
            )
            logger.exception(msg=msg)
            raise FileNotFoundError(msg)

        return exe

    def cli_cmd(self) -> None:
        """Run mayapy with computed args and env."""
        self.configure_logging()
        if self.create_prefix_sitecustomize:
            self.create_sitecustomize()
            return

        args = [self._computed_executable.as_posix(), *self.args]
        _ = call(
            args=args,
            env=self.env,
        )
