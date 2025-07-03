# Copyright (C) 2025 Henrik Wilhelmsen.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at <https://mozilla.org/MPL/2.0/>.

"""Devin DCC Blender bootstrap script.

Credit to https://github.com/friedererdmann/blender_studio_scripts/
and the https://www.tech-artists.org/ Slack for info on how to deal with multiple
BLENDER_USER_SCRIPTS.
"""

import logging
import os
import site
import sys

logger = logging.getLogger("devin_bootstrap")
logging.basicConfig(level=os.environ.get("DEVIN_LOG_LEVEL"))


BLENDER_USER_SCRIPTS = "BLENDER_USER_SCRIPTS"
BLENDER_SITE_PATH = "BLENDER_SITE_PATH"


def add_extra_site_dirs() -> None:
    """Add extra site directories to Blender site-path."""
    extra_site_dirs = os.getenv(BLENDER_SITE_PATH)

    if extra_site_dirs is not None:
        directories = extra_site_dirs.split(os.pathsep)

        for d in directories:
            site.addsitedir(d)

        msg = f"Added extra site directories to Blender: {extra_site_dirs}"
        logger.info(msg=msg)
    else:
        logger.debug(
            "%s not set, no extra dependencies added.",
            BLENDER_SITE_PATH,
        )


def unset_blender_user_scripts_envvar() -> None:
    """Unset the BLENDER_USER_SCRIPTS environment variable.

    Let's Blender pick up other user scripts after we are done bootstrapping.
    """
    if os.environ.get(BLENDER_USER_SCRIPTS) is not None:
        del os.environ[BLENDER_USER_SCRIPTS]


def _initialize() -> None:  # pyright: ignore[reportUnusedFunction]
    unset_blender_user_scripts_envvar()
    add_extra_site_dirs()


def register() -> None:
    """Run the bootstrap functionality.

    Runs automatically when Blender starts up.
    """
    mod = sys.modules[__name__]
    _initialize = getattr(mod, "_initialize", None)

    if _initialize is not None:
        _initialize()
        del mod._initialize  # type: ignore[misc] # noqa: SLF001 # pyright: ignore[reportAttributeAccessIssue]


def unregister() -> None:  # noqa: D103
    pass
