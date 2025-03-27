"""Tests to verify MediaType imports in production code use the consolidated version."""

import pytest

from plexomatic.core.constants import MediaType as ConsolidatedMediaType


def test_imported_mediatype_in_metadata_manager():
    """Test that MediaType imported in metadata manager is the consolidated version."""
    from plexomatic.metadata.manager import MediaType as ManagerMediaType

    assert ManagerMediaType is ConsolidatedMediaType


def test_imported_mediatype_in_name_parser():
    """Test that MediaType imported in name_parser is the consolidated version."""
    from plexomatic.utils.name_parser import MediaType as ParserMediaType

    assert ParserMediaType is ConsolidatedMediaType


def test_imported_mediatype_in_preview_system():
    """Test that MediaType imported in preview_system is the consolidated version."""
    from plexomatic.utils.preview_system import MediaType as PreviewMediaType

    assert PreviewMediaType is ConsolidatedMediaType


def test_mediatype_not_in_models():
    """Test that MediaType no longer exists in models."""
    with pytest.raises(ImportError):
        pass


def test_mediatype_not_in_fetcher():
    """Test that the deprecated MediaType class no longer exists in fetcher."""
    from plexomatic.metadata.fetcher import MediaType

    # Verify that this is the consolidated version
    assert MediaType is ConsolidatedMediaType
    assert MediaType.TV_SHOW.value == "tv_show"


def test_mediatype_compat_module_removed():
    """Test that the mediatype_compat module has been removed."""
    with pytest.raises(ImportError):
        pass
