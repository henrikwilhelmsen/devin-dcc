# Copyright (C) 2025 Henrik Wilhelmsen.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at <https://mozilla.org/MPL/2.0/>.

"""Devin DCC main CLI command."""

import logging
from typing import ClassVar

from pydantic_settings import (
    BaseSettings,
    CliApp,
    CliSubCommand,
    SettingsConfigDict,
)

from devin.cli.blender import Blender
from devin.cli.cleanup import ClearResources
from devin.cli.maya import Maya, Mayapy
from devin.cli.mobu import Mobu, Mobupy

logger: logging.Logger = logging.getLogger(name=__name__)


class Devin(BaseSettings):
    """Devin DCC - CLI tool to launch DCC software."""

    model_config: ClassVar[SettingsConfigDict] = SettingsConfigDict(
        cli_parse_args=True,
        cli_kebab_case=True,
        env_prefix="DEVIN_",
        env_nested_delimiter="__",
    )

    maya: CliSubCommand[Maya]
    mayapy: CliSubCommand[Mayapy]
    mobu: CliSubCommand[Mobu]
    mobupy: CliSubCommand[Mobupy]
    blender: CliSubCommand[Blender]
    clear_resources: CliSubCommand[ClearResources]

    def cli_cmd(self) -> None:
        """Devin CLI command.

        Set up logging and run sub-command.
        """
        _ = CliApp.run_subcommand(self)
