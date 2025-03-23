#!/usr/bin/env python3
"""Standalone test for media_type_compat module."""

import sys
import types
from pathlib import Path

# Add the root directory to the path
sys.path.insert(0, str(Path(__file__).parent))


# Setup mock modules before importing anything
def setup_mocks():
    """Set up mock modules for testing."""
    # Create mock module for name_templates
    mock_name_templates = types.ModuleType("plexomatic.utils.name_templates")
    sys.modules["plexomatic.utils.name_templates"] = mock_name_templates

    # Create a minimal version of constants with MockMediaType
    mock_constants = types.ModuleType("plexomatic.core.constants")

    # Define MockMediaType class inside the mock module
    class MockMediaType:
        """Mock MediaType enum for testing."""

        TV_SHOW = "tv_show"
        TV_SPECIAL = "tv_special"
        MOVIE = "movie"
        ANIME = "anime"
        ANIME_SPECIAL = "anime_special"
        MUSIC = "music"
        UNKNOWN = "unknown"

        def __init__(self, value):
            self.value = value

        @classmethod
        def from_legacy_value(cls, value, source="core"):
            """Mock from_legacy_value implementation."""
            if source == "core":
                mapping = {
                    1: "tv_show",
                    2: "movie",
                    3: "anime",
                    4: "tv_special",
                    5: "anime_special",
                    6: "unknown",
                }
            else:  # fetcher
                mapping = {1: "tv_show", 2: "movie", 3: "anime", 4: "music", 5: "unknown"}
            return cls(mapping.get(value, "unknown"))

        def __eq__(self, other):
            if isinstance(other, MockMediaType):
                return self.value == other.value
            return False

    # Assign MockMediaType to the constants module
    mock_constants.MediaType = MockMediaType
    sys.modules["plexomatic.core.constants"] = mock_constants

    # Return the MockMediaType class for use in tests
    return MockMediaType


# Set up the mock modules
MockMediaType = setup_mocks()

# Now we can import the module under test
# ruff: noqa: E402
from plexomatic.utils.media_type_compat import (
    CoreMediaTypeCompat,
    ParserMediaTypeCompat,
    FetcherMediaTypeCompat,
)


def test_core_media_type_compat():
    """Test CoreMediaTypeCompat class."""
    # Test creation
    tv_show = CoreMediaTypeCompat.TV_SHOW
    assert tv_show._value_ == 1

    # Test comparison with consolidated enum
    assert tv_show._consolidated.value == "tv_show"

    # Test string representation
    assert str(tv_show) == str(MockMediaType("tv_show"))

    print("CoreMediaTypeCompat tests passed")


def test_parser_media_type_compat():
    """Test ParserMediaTypeCompat class."""
    # Test creation
    tv_show = ParserMediaTypeCompat.TV_SHOW
    assert tv_show._value_ == "tv_show"

    # Test comparison with consolidated enum
    assert tv_show._consolidated.value == "tv_show"

    # Test string representation
    assert str(tv_show) == str(MockMediaType("tv_show"))

    print("ParserMediaTypeCompat tests passed")


def test_fetcher_media_type_compat():
    """Test FetcherMediaTypeCompat class."""
    # Test creation
    tv_show = FetcherMediaTypeCompat.TV_SHOW
    assert tv_show._value_ == 1

    # Test comparison with consolidated enum
    assert tv_show._consolidated.value == "tv_show"

    # Test string representation
    assert str(tv_show) == str(MockMediaType("tv_show"))

    print("FetcherMediaTypeCompat tests passed")


if __name__ == "__main__":
    test_core_media_type_compat()
    test_parser_media_type_compat()
    test_fetcher_media_type_compat()
    print("All tests passed!")
