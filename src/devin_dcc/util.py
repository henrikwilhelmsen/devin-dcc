# Copyright (C) 2025 Henrik Wilhelmsen.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at <https://mozilla.org/MPL/2.0/>.

"""Devin DCC utilities."""

from pathlib import Path

from devin_dcc.constants import DEVIN_ROOT_DIR


def get_user_root_dir() -> Path:
    """Get the user root dir, creating it if it doesn't exist."""
    if not DEVIN_ROOT_DIR.exists():
        DEVIN_ROOT_DIR.mkdir(parents=True)
    return DEVIN_ROOT_DIR
