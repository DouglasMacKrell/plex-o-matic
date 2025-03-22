"""Tests for the consolidated MediaType enum."""

import unittest
import json

# Import the current implementations for comparison
from plexomatic.utils.name_parser import MediaType as ParserMediaType

# We'll import the new consolidated MediaType from core.constants
# This doesn't exist yet, but we're writing the test first (TDD)
# The import will fail until we create it
try:
    from plexomatic.core.constants import MediaType
except ImportError:
    # For test development, temporarily alias one of the existing implementations
    MediaType = ParserMediaType


class TestConsolidatedMediaType(unittest.TestCase):
    """Test case for the consolidated MediaType enum."""

    def test_enum_values(self):
        """Test that all necessary enum values are present."""
        # The consolidated enum should have all values from all implementations
        self.assertTrue(hasattr(MediaType, "TV_SHOW"))
        self.assertTrue(hasattr(MediaType, "MOVIE"))
        self.assertTrue(hasattr(MediaType, "ANIME"))
        self.assertTrue(hasattr(MediaType, "TV_SPECIAL"))
        self.assertTrue(hasattr(MediaType, "ANIME_SPECIAL"))
        self.assertTrue(hasattr(MediaType, "MUSIC"))
        self.assertTrue(hasattr(MediaType, "UNKNOWN"))

    def test_string_values(self):
        """Test that enum values are strings for better readability and stability."""
        self.assertEqual(MediaType.TV_SHOW.value, "tv_show")
        self.assertEqual(MediaType.MOVIE.value, "movie")
        self.assertEqual(MediaType.ANIME.value, "anime")
        self.assertEqual(MediaType.TV_SPECIAL.value, "tv_special")
        self.assertEqual(MediaType.ANIME_SPECIAL.value, "anime_special")
        self.assertEqual(MediaType.MUSIC.value, "music")
        self.assertEqual(MediaType.UNKNOWN.value, "unknown")

    def test_serialization(self):
        """Test serialization to JSON."""
        # Serializing an enum to JSON should result in a string
        data = {"media_type": MediaType.TV_SHOW}
        json_str = json.dumps({"media_type": MediaType.TV_SHOW.value})
        self.assertEqual(
            json.dumps(data, default=lambda x: x.value if isinstance(x, MediaType) else x), json_str
        )

    def test_deserialization(self):
        """Test deserialization from various formats."""
        # Test creating from string values (name_parser style)
        self.assertEqual(MediaType("tv_show"), MediaType.TV_SHOW)
        self.assertEqual(MediaType("movie"), MediaType.MOVIE)

        # Test creating from integer values (old core.models style)
        self.assertEqual(MediaType.from_legacy_value(1, "core"), MediaType.TV_SHOW)
        self.assertEqual(MediaType.from_legacy_value(2, "core"), MediaType.MOVIE)

        # Test creating from integer values (old fetcher style)
        self.assertEqual(MediaType.from_legacy_value(1, "fetcher"), MediaType.TV_SHOW)
        self.assertEqual(MediaType.from_legacy_value(2, "fetcher"), MediaType.MOVIE)

    def test_backward_compatibility(self):
        """Test backward compatibility with existing code."""
        # Test comparison with name_parser.MediaType
        self.assertEqual(MediaType.TV_SHOW.name, ParserMediaType.TV_SHOW.name)
        self.assertEqual(MediaType.TV_SHOW.value, ParserMediaType.TV_SHOW.value)

        # Test compatibility properties
        self.assertEqual(
            MediaType.TV_SHOW.core_value, 1
        )  # Assuming TV_SHOW is the first in CoreMediaType
        self.assertEqual(
            MediaType.MOVIE.core_value, 2
        )  # Assuming MOVIE is the second in CoreMediaType

    def test_from_string_method(self):
        """Test the from_string method."""
        # Should handle case insensitivity
        self.assertEqual(MediaType.from_string("tv_show"), MediaType.TV_SHOW)
        self.assertEqual(MediaType.from_string("TV_SHOW"), MediaType.TV_SHOW)
        self.assertEqual(MediaType.from_string("Tv_Show"), MediaType.TV_SHOW)

        # Should handle variations
        self.assertEqual(MediaType.from_string("tvshow"), MediaType.TV_SHOW)
        self.assertEqual(MediaType.from_string("tv"), MediaType.TV_SHOW)

        # Should default to UNKNOWN for unrecognized values
        self.assertEqual(MediaType.from_string("invalid_type"), MediaType.UNKNOWN)


if __name__ == "__main__":
    unittest.main()
