"""Tests package for plexomatic."""

import sys
from pathlib import Path

# Add the parent directory to sys.path to ensure tests can import the package
parent_dir = str(Path(__file__).parent.parent.absolute())
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
