"""Tests package for plexomatic."""

import os
import sys
from pathlib import Path

# Add the parent directory to sys.path to ensure tests can import the package
parent_dir = str(Path(__file__).parent.parent.absolute())
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Add a direct import of plexomatic to verify it can be found
try:
    import plexomatic

    print(f"Successfully imported plexomatic from {plexomatic.__file__}")
except ImportError as e:
    print(f"WARNING: Failed to import plexomatic: {e}")

# Make all test modules available as part of the tests package
__all__ = []
for file in os.listdir(os.path.dirname(__file__)):
    if file.startswith("test_") and file.endswith(".py"):
        __all__.append(file[:-3])  # Remove .py extension

print(f"tests/__init__.py loaded, found {len(__all__)} test modules")
