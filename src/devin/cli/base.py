# Copyright (C) 2025 Henrik Wilhelmsen.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at <https://mozilla.org/MPL/2.0/>.

"""Devin DCC cli base command."""

import logging
import logging.config
import os
import sys
from distutils.sysconfig import get_python_lib
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
    """Base command model."""

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

    def configure_logging(self) -> None:
        """Configure logging for the CLI."""
        logging_config: dict[
            str,
            int
            | bool
            | dict[str, dict[str, str]]
            | dict[str, dict[str, str | list[str]]],
        ] = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "simple": {
                    "format": "%(levelname)s: %(message)s",
                },
                "detailed": {
                    "format": "[%(levelname)s|%(module)s|L%(lineno)d] %(asctime)s: %(message)s",  # noqa: E501
                    "datefmt": "%Y-%m-%dT%H:%M:%S%z",
                },
            },
            "handlers": {
                "stdout": {
                    "class": "logging.StreamHandler",
                    "level": self.log_level,
                    "formatter": "simple",
                    "stream": "ext://sys.stdout",
                },
            },
            "loggers": {"root": {"level": "DEBUG", "handlers": ["stdout"]}},
        }
        logging.config.dictConfig(logging_config)
        os.environ["DEVIN_LOG_LEVEL"] = self.log_level


class BaseDCCCommand(BaseCommand):
    """Base command, containing arguments shared between all DCC commands."""

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
    _executable_help: str = (
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
        site_dirs: list[Path] = []
        if self.include_prefix_site:
            site_dirs = [Path(get_python_lib(prefix=sys.prefix))]

        if self.site_path:
            site_dirs.extend(self.site_path)

        if site_dirs:
            return ";".join([x.as_posix() for x in site_dirs])

        return None
