# Copyright (C) 2025 Henrik Wilhelmsen.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at <https://mozilla.org/MPL/2.0/>.

"""Devin DCC Blender bootstrap script."""

import logging
import os
import site

logger = logging.getLogger("devin_bootstrap")
logging.basicConfig(level=os.environ.get("DEVIN_LOG_LEVEL"))

MOBU_SITE_PATH = "MOTIONBUILDER_SITE_PATH"


def add_extra_site_dirs() -> None:
    """Add extra site directories to Motionbuilder site-packages."""
    extra_site_dirs = os.getenv(MOBU_SITE_PATH)

    if extra_site_dirs is not None:
        directories = extra_site_dirs.split(";")

        for d in directories:
            site.addsitedir(d)

        msg = f"Added extra site directories: {extra_site_dirs}"
        logger.info(msg=msg)
    else:
        logger.debug(
            "%s not set, no extra dependencies added.",
            MOBU_SITE_PATH,
        )


add_extra_site_dirs()
