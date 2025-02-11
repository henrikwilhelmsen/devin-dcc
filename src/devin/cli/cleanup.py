# Copyright (C) 2025 Henrik Wilhelmsen.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at <https://mozilla.org/MPL/2.0/>.

"""Devin DCC cli base command."""

import logging
from shutil import rmtree

from devin.cli.base import BaseCommand
from devin.constants import DEVIN_RESOURCE_DIR

logger = logging.getLogger(__name__)


class ClearResources(BaseCommand):
    """Clear the local resources directory (where downloads are stored)."""

    def cli_cmd(self) -> None:
        """CLI command to clear local resources directory."""
        self.configure_logging()
        if not DEVIN_RESOURCE_DIR.is_dir():
            logger.info(
                "Local resources directory %s is already deleted",
                DEVIN_RESOURCE_DIR,
            )
            return

        try:
            rmtree(DEVIN_RESOURCE_DIR)
        except OSError:
            logger.warning(
                "Failed to clear local resources directory %s",
                DEVIN_RESOURCE_DIR,
            )
            return

        logger.info("Cleared local resources directory %s", DEVIN_RESOURCE_DIR)
