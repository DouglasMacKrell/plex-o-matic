"""Compatibility module for MediaType transition.

This module provides backward compatibility during the transition
from multiple MediaType implementations to the unified one.

Usage:
    # For new code, use the consolidated MediaType directly:
    from plexomatic.core.constants import MediaType

    # For backward compatibility with existing imports:
    from plexomatic.utils.name_parser import MediaType  # Will redirect to consolidated version
"""

import warnings
import enum
from typing import Any, Type, TypeVar, Optional, Union

# Import the consolidated MediaType
from plexomatic.core.constants import MediaType as ConsolidatedMediaType

T = TypeVar("T", bound="CoreMediaTypeCompat")
T2 = TypeVar("T2", bound="ParserMediaTypeCompat")
T3 = TypeVar("T3", bound="FetcherMediaTypeCompat")


# Backward compatibility for core.models.MediaType
class CoreMediaTypeCompat(enum.Enum):
    """Compatibility class for core.models.MediaType."""

    TV_SHOW = 1
    MOVIE = 2
    ANIME = 3
    TV_SPECIAL = 4
    ANIME_SPECIAL = 5
    UNKNOWN = 6

    # Class variable to store the consolidated MediaType instance
    # Note: In Python 3.8+, instance attributes can be set in __new__
    # The type annotation is now just to document the expected type
    _consolidated: ConsolidatedMediaType

    def __new__(cls: Type[T], value: int) -> T:
        """Create a new instance of the enum.

        Args:
            value: The integer value for this enum member

        Returns:
            A new enum instance
        """
        obj = object.__new__(cls)
        obj._value_ = value
        # Store a reference to the consolidated enum instance as an instance attribute
        obj._consolidated = ConsolidatedMediaType.from_legacy_value(value, "core")
        return obj

    def __eq__(self, other: Any) -> bool:
        """Compare equality, handling comparison with consolidated enum.

        Args:
            other: The object to compare with

        Returns:
            True if equal, False otherwise
        """
        if isinstance(other, ConsolidatedMediaType):
            return self._consolidated == other
        return super().__eq__(other)

    def __str__(self) -> str:
        """Return string representation.

        Returns:
            String representation of this enum member
        """
        return str(self._consolidated)

    def __repr__(self) -> str:
        """Return repr string.

        Returns:
            String representation for debugging
        """
        return repr(self._consolidated)

    @classmethod
    def from_string(cls, value: str) -> "CoreMediaTypeCompat":
        """Convert a string value to a MediaType enum value.

        Args:
            value: The string value to convert

        Returns:
            The corresponding MediaType enum value
        """
        warnings.warn(
            "core.models.MediaType.from_string is deprecated. Use core.constants.MediaType.from_string instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        # Get the consolidated version first
        consolidated = ConsolidatedMediaType.from_string(value)
        # Find the corresponding legacy value
        for member in cls:
            if member._consolidated == consolidated:
                return member
        return cls.UNKNOWN


# Backward compatibility for name_parser.MediaType
class ParserMediaTypeCompat(enum.Enum):
    """Compatibility class for name_parser.MediaType."""

    TV_SHOW = "tv_show"
    TV_SPECIAL = "tv_special"
    MOVIE = "movie"
    ANIME = "anime"
    ANIME_SPECIAL = "anime_special"
    UNKNOWN = "unknown"

    # Class variable to store the consolidated MediaType instance
    # Note: In Python 3.8+, instance attributes can be set in __new__
    # The type annotation is now just to document the expected type
    _consolidated: ConsolidatedMediaType

    def __new__(cls: Type[T2], value: str) -> T2:
        """Create a new instance of the enum.

        Args:
            value: The string value for this enum member

        Returns:
            A new enum instance
        """
        obj = object.__new__(cls)
        obj._value_ = value
        # Store a reference to the consolidated enum instance as an instance attribute
        obj._consolidated = ConsolidatedMediaType(value)
        return obj

    def __eq__(self, other: Any) -> bool:
        """Compare equality, handling comparison with consolidated enum.

        Args:
            other: The object to compare with

        Returns:
            True if equal, False otherwise
        """
        if isinstance(other, ConsolidatedMediaType):
            return self._consolidated == other
        return super().__eq__(other)

    def __str__(self) -> str:
        """Return string representation.

        Returns:
            String representation of this enum member
        """
        return str(self._consolidated)

    def __repr__(self) -> str:
        """Return repr string.

        Returns:
            String representation for debugging
        """
        return repr(self._consolidated)


# Backward compatibility for fetcher.MediaType
class FetcherMediaTypeCompat(enum.Enum):
    """Compatibility class for metadata.fetcher.MediaType."""

    TV_SHOW = 1
    MOVIE = 2
    ANIME = 3
    MUSIC = 4
    UNKNOWN = 5

    # Class variable to store the consolidated MediaType instance
    # Note: In Python 3.8+, instance attributes can be set in __new__
    # The type annotation is now just to document the expected type
    _consolidated: ConsolidatedMediaType

    def __new__(cls: Type[T3], value: int) -> T3:
        """Create a new instance of the enum.

        Args:
            value: The integer value for this enum member

        Returns:
            A new enum instance
        """
        obj = object.__new__(cls)
        obj._value_ = value
        # Store a reference to the consolidated enum instance as an instance attribute
        obj._consolidated = ConsolidatedMediaType.from_legacy_value(value, "fetcher")
        return obj

    def __eq__(self, other: Any) -> bool:
        """Compare equality, handling comparison with consolidated enum.

        Args:
            other: The object to compare with

        Returns:
            True if equal, False otherwise
        """
        if isinstance(other, ConsolidatedMediaType):
            return self._consolidated == other
        return super().__eq__(other)

    def __str__(self) -> str:
        """Return string representation.

        Returns:
            String representation of this enum member
        """
        return str(self._consolidated)

    def __repr__(self) -> str:
        """Return repr string.

        Returns:
            String representation for debugging
        """
        return repr(self._consolidated)


# Deprecated imports for backward compatibility
def get_media_type(value: Optional[Union[str, int]]) -> Optional[ConsolidatedMediaType]:
    """Convert a string or int to a MediaType enum value.

    Args:
        value: String or int to convert

    Returns:
        MediaType enum value or None if not found
    """
    if value is None:
        return None

    # Handle string values
    if isinstance(value, str):
        value = value.upper()
        try:
            return ConsolidatedMediaType[value]
        except KeyError:
            pass

    # Handle integer values
    if isinstance(value, int):
        try:
            return ConsolidatedMediaType(value)
        except ValueError:
            pass

    return None
