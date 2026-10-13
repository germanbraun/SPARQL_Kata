"""Allows `python -m sparql_kata ...`."""

import sys

from .cli import main

sys.exit(main())
