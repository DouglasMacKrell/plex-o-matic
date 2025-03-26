"""Tests for the preview system module."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List
import csv

import pytest
from unittest.mock import MagicMock

from plexomatic.core.constants import MediaType
from plexomatic.utils.preview_system import (
    PreviewGenerator,
    DiffDisplay,
    BatchPreview,
    PreviewExporter,
    PreviewResult,
    DiffStyle,
)


@pytest.fixture
def sample_media_files(tmpdir) -> List[str]:
    """Create sample media files for testing."""
    # Create TV Shows directory
    tv_dir = os.path.join(tmpdir, "TV Shows")
    os.makedirs(tv_dir, exist_ok=True)

    # Create files in TV Shows directory
    tv_files = [
        os.path.join(tv_dir, "Show.Name.S01E01.Episode.Title.mkv"),
        os.path.join(tv_dir, "Another.Show.S02E05.Some.Title.mp4"),
        os.path.join(tv_dir, "Old_Format_1x03_Title.avi"),
    ]

    # Create Movies directory
    movie_dir = os.path.join(tmpdir, "Movies")
    os.makedirs(movie_dir, exist_ok=True)

    # Create files in Movies directory
    movie_files = [
        os.path.join(movie_dir, "Movie.Name.2020.mp4"),
        os.path.join(movie_dir, "Another.Movie.2019.mkv"),
    ]

    # Create empty files
    for file_path in tv_files + movie_files:
        open(file_path, "w").close()

    # Convert paths to str for consistency
    return [str(path) for path in tv_files + movie_files]


@pytest.fixture
def preview_results() -> List[PreviewResult]:
    """Create sample preview results for testing."""
    return [
        PreviewResult(
            original_path=Path("/TV Shows/Show.Name.S01E01.Episode.Title.mkv"),
            new_path=Path("/TV Shows/Show Name/Season 01/Show Name - S01E01 - Episode Title.mkv"),
            media_type=MediaType.TV_SHOW,
            confidence=0.95,
            metadata={
                "show_name": "Show Name",
                "season": 1,
                "episode": 1,
                "title": "Episode Title",
            },
        ),
        PreviewResult(
            original_path=Path("/TV Shows/Another.Show.S02E05.Some.Title.mp4"),
            new_path=Path(
                "/TV Shows/Another Show/Season 02/Another Show - S02E05 - Some Title.mp4"
            ),
            media_type=MediaType.TV_SHOW,
            confidence=0.92,
            metadata={
                "show_name": "Another Show",
                "season": 2,
                "episode": 5,
                "title": "Some Title",
            },
        ),
        PreviewResult(
            original_path=Path("/Movies/Movie.Name.2020.mp4"),
            new_path=Path("/Movies/Movie Name (2020)/Movie Name (2020).mp4"),
            media_type=MediaType.MOVIE,
            confidence=0.88,
            metadata={"title": "Movie Name", "year": 2020},
        ),
    ]


class TestPreviewGenerator:
    """Tests for the PreviewGenerator class."""

    def test_generate_preview_for_file(self, sample_media_files: List[str]) -> None:
        """Test generating a preview for a single file."""
        generator = PreviewGenerator()
        result = generator.generate_preview_for_file(sample_media_files[0])

        assert isinstance(result, PreviewResult)
        assert result.original_path == Path(sample_media_files[0])
        assert result.new_path is not None
        assert result.media_type is not None
        assert result.confidence > 0

    def test_generate_preview_for_directory(
        self, sample_media_files: List[str], tmpdir: Path
    ) -> None:
        """Test generating previews for a directory."""
        generator = PreviewGenerator()
        results = generator.generate_preview_for_directory(tmpdir)

        assert len(results) == len(sample_media_files)
        assert all(isinstance(result, PreviewResult) for result in results)

    def test_filter_results_by_media_type(self, preview_results: List[PreviewResult]) -> None:
        """Test filtering preview results by media type."""
        generator = PreviewGenerator()
        # Mock generate_preview_for_directory to return our fixture data
        generator.generate_preview_for_directory = MagicMock(return_value=preview_results)

        mock_dir = Path("/some/dir")
        all_results = generator.generate_preview_for_directory(mock_dir)
        tv_results = generator.filter_results_by_media_type(all_results, MediaType.TV_SHOW)

        assert len(tv_results) == 2
        assert all(result.media_type == MediaType.TV_SHOW for result in tv_results)

    def test_sort_results(self, preview_results: List[PreviewResult]) -> None:
        """Test sorting preview results."""
        generator = PreviewGenerator()

        # Sort by confidence
        sorted_by_confidence = generator.sort_results(preview_results, "confidence", reverse=True)
        assert sorted_by_confidence[0].confidence >= sorted_by_confidence[1].confidence

        # Sort by media_type
        sorted_by_type = generator.sort_results(preview_results, "media_type")
        # Since we have MOVIE and TV_SHOW, and TV_SHOW comes first alphabetically in the enum value list
        assert sorted_by_type[0].media_type == MediaType.TV_SHOW


class TestDiffDisplay:
    """Tests for the DiffDisplay class."""

    def test_generate_diff_string(self, preview_results: List[PreviewResult]) -> None:
        """Test generating a diff string for a preview result."""
        display = DiffDisplay()
        result = preview_results[0]

        # Test side-by-side diff
        diff_side_by_side = display.generate_diff_string(result, DiffStyle.SIDE_BY_SIDE)
        assert result.original_path.name in diff_side_by_side
        assert result.new_path.name in diff_side_by_side

        # Test unified diff
        diff_unified = display.generate_diff_string(result, DiffStyle.UNIFIED)
        assert result.original_path.name in diff_unified
        assert result.new_path.name in diff_unified

        # Test minimal diff
        diff_minimal = display.generate_diff_string(result, DiffStyle.MINIMAL)
        assert result.original_path.name in diff_minimal
        assert result.new_path.name in diff_minimal

    def test_color_output(self, preview_results: List[PreviewResult]) -> None:
        """Test that color output works correctly."""
        display = DiffDisplay(color_mode=True)
        result = preview_results[0]

        diff_with_color = display.generate_diff_string(result, DiffStyle.SIDE_BY_SIDE)

        # Should have ANSI color codes
        assert "\033[" in diff_with_color

        # Without color
        display.color_mode = False
        diff_without_color = display.generate_diff_string(result, DiffStyle.SIDE_BY_SIDE)

        # Should not have ANSI color codes
        assert "\033[" not in diff_without_color


class TestBatchPreview:
    """Tests for the BatchPreview class."""

    def test_create_batch_groups(self, preview_results: List[PreviewResult]) -> None:
        """Test creating batch groups from preview results."""
        batch = BatchPreview()
        groups = batch.create_batch_groups(preview_results)

        # Should have grouped by media_type (TV_SHOW and MOVIE)
        assert len(groups) == 2

        # Check that each group has the correct media_type
        for group_name, group_results in groups.items():
            assert all(result.media_type.value == group_name for result in group_results)

    def test_generate_table(self, preview_results: List[PreviewResult]) -> None:
        """Test generating a table for batch preview."""
        batch = BatchPreview()
        table = batch.generate_table(preview_results)

        # Table should be a string
        assert isinstance(table, str)

        # Table should contain all original and new filenames
        for result in preview_results:
            assert result.original_path.name in table
            assert result.new_path.name in table


class TestPreviewExporter:
    """Tests for the PreviewExporter class."""

    def test_export_to_json(self, preview_results: List[PreviewResult], tmpdir: Path) -> None:
        """Test exporting preview results to JSON."""
        exporter = PreviewExporter()
        output_file = tmpdir / "preview_results.json"

        exporter.export_to_json(preview_results, output_file)

        # Check that file exists
        assert output_file.exists()

        # Check that file contains valid JSON
        with open(output_file, "r") as f:
            data = json.load(f)

        # Should have the same number of entries
        assert len(data) == len(preview_results)

    def test_export_to_csv(self, preview_results: List[PreviewResult], tmpdir: Path) -> None:
        """Test exporting preview results to CSV."""
        exporter = PreviewExporter()
        output_file = tmpdir / "preview_results.csv"

        exporter.export_to_csv(preview_results, output_file)

        # Check that file exists
        assert output_file.exists()

        # Check that file contains valid CSV
        with open(output_file, "r") as f:
            reader = csv.reader(f)
            rows = list(reader)

        # Should have a header row + one row per preview result
        assert len(rows) == len(preview_results) + 1

    def test_import_from_json(self, preview_results: List[PreviewResult], tmpdir: Path) -> None:
        """Test importing preview results from JSON."""
        exporter = PreviewExporter()
        output_file = tmpdir / "preview_results.json"

        # First export
        exporter.export_to_json(preview_results, output_file)

        # Then import
        imported_results = exporter.import_from_json(output_file)

        # Should have the same number of entries
        assert len(imported_results) == len(preview_results)

        # Check that each entry has the correct data
        for i, result in enumerate(preview_results):
            assert imported_results[i].original_path == result.original_path
            assert imported_results[i].new_path == result.new_path

            # Compare the names of the MediaType enums instead of the objects directly
            # This handles the difference between MediaType from name_parser and core.models
            assert imported_results[i].media_type.name == result.media_type.name

            assert imported_results[i].confidence == result.confidence

            # Check metadata if present
            if result.metadata:
                assert imported_results[i].metadata == result.metadata
