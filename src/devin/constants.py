# Copyright (C) 2025 Henrik Wilhelmsen.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at <https://mozilla.org/MPL/2.0/>.

"""Devin DCC application constants."""

from pathlib import Path
from typing import Literal

DATA_DIR = Path(__file__).parent / "data"

# Supported platforms, following platform.system() return values
PLATFORMS = Literal["Linux", "Windows"]

DEVIN_ROOT_DIR = Path.home() / "devin-dcc"
DEVIN_RESOURCE_DIR = DEVIN_ROOT_DIR / "resource"
DEVIN_LOG_FILE: Path = DEVIN_ROOT_DIR / "log.txt"
