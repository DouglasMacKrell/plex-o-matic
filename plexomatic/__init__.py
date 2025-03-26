"""
Plex-o-matic: An intelligent media file organization tool for Plex
"""

from importlib.metadata import version, PackageNotFoundError

# Package metadata
__app_name__ = "plex-o-matic"
try:
    __version__ = version(__app_name__)
except PackageNotFoundError:  # pragma: no cover
    __version__ = "unknown"

# Expose CLI entry point directly for simple imports
