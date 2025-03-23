# MediaType Consolidation

This document describes the MediaType enum consolidation process in Plex-o-matic and how the compatibility layers work.

## Overview

Plex-o-matic originally had multiple implementations of the MediaType enum in different modules:

1. `plexomatic.utils.name_parser.MediaType` - Used string values like "tv_show"
2. `plexomatic.core.models.MediaType` - Used auto-generated integer values
3. `plexomatic.metadata.fetcher.MediaType` - Used integer values with different numbering

This duplication created several issues:
- Type incompatibility between modules
- Maintenance burden
- Cognitive overhead for developers
- Testing complexity
- Documentation confusion

## Consolidation

We've consolidated these enums into a single definition in `plexomatic.core.constants.MediaType` while maintaining backward compatibility through compatibility layers.

### Consolidated MediaType

The consolidated MediaType enum uses string values, which are more readable and stable:

```python
class MediaType(str, Enum):
    """Media type enum for categorizing media files."""

    TV_SHOW = "tv_show"
    TV_SPECIAL = "tv_special"
    MOVIE = "movie"
    ANIME = "anime"
    ANIME_SPECIAL = "anime_special"
    UNKNOWN = "unknown"

    @classmethod
    def from_legacy_value(cls, value: Union[int, str], source: str) -> "MediaType":
        """Convert legacy integer or string values to the consolidated enum."""
        ...
```

## Compatibility Layers

To maintain backward compatibility, we've implemented compatibility layers in `plexomatic.utils.media_type_compat`:

### CoreMediaTypeCompat

This provides compatibility with the original core.models.MediaType:

```python
class CoreMediaTypeCompat(enum.Enum):
    """Compatibility class for core.models.MediaType."""

    TV_SHOW = 1
    TV_SPECIAL = 2
    MOVIE = 3
    ANIME = 4
    ANIME_SPECIAL = 5
    UNKNOWN = 6

    # Each instance holds a reference to the consolidated MediaType
    _consolidated: ConsolidatedMediaType
```

### ParserMediaTypeCompat

This provides compatibility with the original name_parser.MediaType:

```python
class ParserMediaTypeCompat(enum.Enum):
    """Compatibility class for name_parser.MediaType."""

    TV_SHOW = "tv_show"
    TV_SPECIAL = "tv_special"
    MOVIE = "movie"
    ANIME = "anime"
    ANIME_SPECIAL = "anime_special"
    UNKNOWN = "unknown"

    # Each instance holds a reference to the consolidated MediaType
    _consolidated: ConsolidatedMediaType
```

### FetcherMediaTypeCompat

This provides compatibility with the original fetcher.MediaType:

```python
class FetcherMediaTypeCompat(enum.Enum):
    """Compatibility class for metadata.fetcher.MediaType."""

    TV = 1
    MOVIE = 2
    ANIME = 3
    SPECIAL = 4
    UNKNOWN = 5

    # Each instance holds a reference to the consolidated MediaType
    _consolidated: ConsolidatedMediaType
```

## Implementation Details

Each compatibility enum:
1. Uses the same values as the original enum
2. Stores a reference to the consolidated MediaType in each instance
3. Provides magic methods for comparison with other enum types
4. Includes a `consolidated()` method to access the underlying consolidated enum
5. Uses proper type annotations to satisfy mypy

## Usage

### Direct Usage

Use the consolidated MediaType directly:

```python
from plexomatic.core.constants import MediaType

media_type = MediaType.TV_SHOW
```

### For Legacy Code

Use the compatibility layers for legacy code:

```python
from plexomatic.utils.media_type_compat import CoreMediaTypeCompat

# Create a compatible enum
media_type = CoreMediaTypeCompat.TV_SHOW

# Convert to the consolidated type
consolidated = media_type.consolidated()
```

## Forward Compatibility

When working with code that expects a specific enum:

```python
from plexomatic.core.constants import MediaType
from plexomatic.utils.media_type_compat import CoreMediaTypeCompat

# Starting with consolidated MediaType
consolidated = MediaType.TV_SHOW

# Convert to legacy type for compatibility
legacy = CoreMediaTypeCompat.from_consolidated(consolidated)
```

## Conclusion

The MediaType consolidation and compatibility layers ensure that:
1. New code can use a single, consistent MediaType enum
2. Legacy code continues to work with the expected enum values
3. Type checking works correctly across the codebase
4. Enums can be easily compared regardless of their source

This approach provides a clean migration path without requiring widespread changes throughout the codebase.
