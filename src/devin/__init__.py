# Copyright (C) 2025 Henrik Wilhelmsen.
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at <https://mozilla.org/MPL/2.0/>.

"""Devin DCC CLI.

CLI Tool to launch DCC software. For usage, install the program with uv, pipx or similar
and run `devin --help`
"""

from pydantic_settings import CliApp

from devin.cli.devin import Devin


def main() -> None:
    """Main entry point for the CLI."""
    _ = CliApp.run(Devin)


if __name__ == "__main__":
    main()
