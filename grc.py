#!/usr/bin/env python3
"""Thin entry point for the GRC Evidence Tracker CLI.

Usage: python3 grc.py [--data PATH] <command> ...
Or install the package (pip install .) and use the `grc-tracker` command.
"""

from grc_tracker.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
