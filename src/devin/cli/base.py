# Copyright (C) 2025 Henrik Wilhelmsen.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at <https://mozilla.org/MPL/2.0/>.

"""Devin DCC cli base command."""

import logging
import os
from typing import Literal

from pydantic import (
    BaseModel,
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

    def configure_logging(self) -> None:
        """Configure logging for the CLI."""
        logging.basicConfig(level=self.log_level)
        os.environ["DEVIN_LOG_LEVEL"] = self.log_level
