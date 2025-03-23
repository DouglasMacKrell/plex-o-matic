"""Central constants for the plexomatic project.

This module contains constants used throughout the project,
including enums and other shared values.
"""

import enum
import warnings

# Maps from legacy enum values to string values
# Core models implementation uses integers (1, 2, 3, etc.)
# Fetcher implementation also uses integers but has different members
CORE_LEGACY_MAPPING = {
    1: "tv_show",
    2: "movie",
    3: "anime",
    4: "tv_special",
    5: "anime_special",
    6: "unknown",
}

FETCHER_LEGACY_MAPPING = {
    1: "tv_show",
    2: "movie",
    3: "anime",
    4: "music",
    5: "unknown",
}


class MediaType(enum.Enum):
    """Unified enum representing types of media.

    This consolidated enum replaces the separate implementations in:
    - plexomatic.utils.name_parser.MediaType
    - plexomatic.core.models.MediaType
    - plexomatic.metadata.fetcher.MediaType

    This enum uses string values for better readability and stability across
    serialization/deserialization operations.
    """

    TV_SHOW = "tv_show"
    TV_SPECIAL = "tv_special"
    MOVIE = "movie"
    ANIME = "anime"
    ANIME_SPECIAL = "anime_special"
    MUSIC = "music"
    UNKNOWN = "unknown"

    @property
    def core_value(self) -> int:
        """Get the legacy integer value used in core.models.MediaType."""
        # Find position in CORE_LEGACY_MAPPING values
        for i, value in CORE_LEGACY_MAPPING.items():
            if value == self.value:
                return i
        return 6  # UNKNOWN

    @property
    def fetcher_value(self) -> int:
        """Get the legacy integer value used in metadata.fetcher.MediaType."""
        # Find position in FETCHER_LEGACY_MAPPING values
        for i, value in FETCHER_LEGACY_MAPPING.items():
            if value == self.value:
                return i
        return 5  # UNKNOWN

    @classmethod
    def from_legacy_value(cls, value: int, source: str = "core") -> "MediaType":
        """Convert a legacy integer value to a MediaType.

        Args:
            value: Integer value from legacy enum implementation
            source: Source of the legacy value ('core' or 'fetcher')

        Returns:
            Corresponding MediaType instance
        """
        if source.lower() == "core":
            str_value = CORE_LEGACY_MAPPING.get(value, "unknown")
            return cls(str_value)
        elif source.lower() == "fetcher":
            str_value = FETCHER_LEGACY_MAPPING.get(value, "unknown")
            return cls(str_value)
        else:
            warnings.warn(f"Unknown legacy source: {source}, defaulting to 'core'")
            str_value = CORE_LEGACY_MAPPING.get(value, "unknown")
            return cls(str_value)

    @classmethod
    def from_string(cls, value: str) -> "MediaType":
        """Convert a string value to a MediaType enum value.

        This method is case-insensitive and handles some common variations.

        Args:
            value: String value to convert

        Returns:
            Corresponding MediaType instance, or UNKNOWN if not recognized
        """
        # Try exact match first
        try:
            return cls(value.lower())
        except ValueError:
            pass

        # Try case-insensitive name matching
        for member in cls:
            if member.name.lower() == value.lower():
                return member

        # Try substring matching for common cases
        value_lower = value.lower()
        if "tv" in value_lower or "show" in value_lower:
            return cls.TV_SHOW
        if "movie" in value_lower or "film" in value_lower:
            return cls.MOVIE
        if "anime" in value_lower:
            return cls.ANIME
        if "special" in value_lower and "anime" in value_lower:
            return cls.ANIME_SPECIAL
        if "special" in value_lower or "ova" in value_lower:
            return cls.TV_SPECIAL
        if "music" in value_lower or "song" in value_lower:
            return cls.MUSIC

        # Default to UNKNOWN
        return cls.UNKNOWN
