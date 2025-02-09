# Copyright (C) 2025 Henrik Wilhelmsen.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at <https://mozilla.org/MPL/2.0/>.

"""Devin DCC cli base command."""

import logging
import os
import sys
from pathlib import Path
from typing import Literal

from pydantic import (
    AliasChoices,
    BaseModel,
    DirectoryPath,
    Field,
    FilePath,
    computed_field,
)
from pydantic_settings import (
    CliImplicitFlag,
)

logger = logging.getLogger(__name__)


class BaseCommand(BaseModel):
    """Base command, containing arguments shared between all CLI commands."""

    log_level: Literal[
        "CRITICAL",
        "FATAL",
        "ERROR",
        "WARN",
        "WARNING",
        "INFO",
        "DEBUG",
        "NOTSET",
    ] = "INFO"

    args: list[str] = Field(
        default_factory=list,
        description="Additional arguments to pass to executable",
    )
    include_prefix_site: CliImplicitFlag[bool] = Field(
        default=False,
        description="Add site-packages dir of current Python env to DCC at launch",
    )
    temp_config_dir: CliImplicitFlag[bool] = Field(
        default=False,
        description="Launch with user config set to an empty temp dir",
    )
    site_path: list[DirectoryPath] = Field(
        default_factory=list,
        description="Extra paths to add to executable's site directories at launch",
    )
    _executable_help = (
        "Optional path to the executable to use. If not set, "
        "the program will search the default install locations."
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

    def configure_logging(self) -> None:
        """Configure logging for the CLI."""
        logging.basicConfig(level=self.log_level)
        os.environ["DEVIN_LOG_LEVEL"] = self.log_level
