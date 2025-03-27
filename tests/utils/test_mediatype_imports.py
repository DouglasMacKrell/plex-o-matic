"""Tests for importing MediaType from different modules."""

import pytest

# Import the consolidated MediaType directly
from plexomatic.core.constants import MediaType as ConsolidatedMediaType


def test_direct_import_from_constants():
    """Test importing MediaType directly from core.constants."""
    from plexomatic.core.constants import MediaType

    # Verify it's the consolidated version
    assert MediaType.TV_SHOW.value == "tv_show"
    assert MediaType.MOVIE.value == "movie"
    assert MediaType.ANIME.value == "anime"
    assert MediaType.TV_SPECIAL.value == "tv_special"
    assert MediaType.ANIME_SPECIAL.value == "anime_special"
    assert MediaType.MUSIC.value == "music"
    assert MediaType.UNKNOWN.value == "unknown"


def test_mediatype_not_in_models():
    """Test that MediaType no longer exists in models."""
    with pytest.raises(ImportError):
        pass


def test_direct_import_from_fetcher():
    """Test importing MediaType from fetcher."""
    from plexomatic.metadata.fetcher import MediaType

    # MediaType should be imported from constants now
    assert MediaType is ConsolidatedMediaType
    assert MediaType.TV_SHOW.value == "tv_show"


def test_mediatype_compat_module_removed():
    """Test that the mediatype_compat module has been removed."""
    with pytest.raises(ImportError):
        pass
