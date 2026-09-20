#!/bin/zsh
# Double-click installer for macOS users who downloaded the GitHub ZIP.
cd -- "$(dirname -- "$0")" || exit 1
exec /usr/bin/env python3 tools/install.py
