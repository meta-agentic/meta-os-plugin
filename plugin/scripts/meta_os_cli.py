#!/usr/bin/env python3
"""Entry point of the `meta-os` command. Standard library only, Python 3.9 or later."""
import sys

from meta_os.cli import main

if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
