"""Subtitle scanner module for identifying and analyzing subtitle files."""

import re
import os
from pathlib import Path
from typing import List, Dict

from plexomatic.core.file_scanner import MediaFile


class SubtitleFile:
    """Represents a subtitle file with its properties and metadata."""

    def __init__(self, path: Path):
        """Initialize a SubtitleFile instance.

        Args:
            path: Path to the subtitle file
        """
        self.path = Path(path)
        self.extension = self.path.suffix.lower()
        self.filename = self.path.stem
        self.language = self._detect_language()
        self.is_forced = self._is_forced()
        self.is_sdh = self._is_sdh()
        self.media_name = self._extract_media_name()

    def _detect_language(self) -> str:
        """Detect language from the filename.

        Returns:
            str: The language code (two or three letters) or 'und' if not detected
        """
        # Check for language code pattern: filename.en.srt or filename.en.forced.srt
        # Matches 2 or 3 letter language codes
        pattern = r"\.([a-z]{2,3})(?:\.(forced|sdh))?$"
        match = re.search(pattern, self.filename, re.IGNORECASE)
        if match:
            return match.group(1).lower()
        return "und"  # undefined language code

    def _is_forced(self) -> bool:
        """Check if subtitle is marked as forced.

        Returns:
            bool: True if the subtitle is forced, False otherwise
        """
        return ".forced" in self.filename.lower() or "forced." in self.filename.lower()

    def _is_sdh(self) -> bool:
        """Check if subtitle is marked as SDH (Subtitles for the Deaf and Hard of hearing).

        Returns:
            bool: True if the subtitle is SDH, False otherwise
        """
        return ".sdh" in self.filename.lower() or "sdh." in self.filename.lower()

    def _extract_media_name(self) -> str:
        """Extract the media file name this subtitle goes with.

        Removes language codes and subtitle flags from the filename.

        Returns:
            str: The base media file name
        """
        # Pattern that matches language code and flag patterns
        # This is more comprehensive to handle complex cases
        # like Comedy.S02E03.en.forced.sdh.srt
        pattern = r"(?:\.([a-z]{2,3}))?(?:\.(forced|sdh))*$"

        # Apply regex to remove language and flags
        media_name = re.sub(pattern, "", self.filename, flags=re.IGNORECASE)
        return media_name


def scan_for_subtitles(directory_path: str, subtitle_extensions: List[str]) -> List[SubtitleFile]:
    """Scan a directory for subtitle files.

    Args:
        directory_path: Path to the directory to scan
        subtitle_extensions: List of subtitle file extensions to look for (e.g., [".srt", ".sub"])

    Returns:
        List of SubtitleFile objects found in the directory
    """
    subtitle_files = []
    directory = Path(directory_path)

    # Convert subtitle extensions to lowercase set for faster lookups
    extensions_set = {ext.lower() for ext in subtitle_extensions}

    # Walk through directory recursively
    for root, _, files in os.walk(directory):
        for file_name in files:
            file_path = Path(root) / file_name

            # Check if file has a subtitle extension
            if file_path.suffix.lower() in extensions_set:
                subtitle_files.append(SubtitleFile(file_path))

    return subtitle_files


def match_subtitles_to_media(
    media_files: List[MediaFile], subtitle_files: List[SubtitleFile]
) -> Dict[MediaFile, List[SubtitleFile]]:
    """Match subtitle files to their corresponding media files.

    Args:
        media_files: List of media files to match subtitles to
        subtitle_files: List of subtitle files to match

    Returns:
        Dictionary mapping media files to lists of matching subtitle files
    """
    matches: Dict[MediaFile, List[SubtitleFile]] = {media_file: [] for media_file in media_files}

    # Extract media file names (without extension) for faster matching
    media_base_names = {media_file: Path(media_file.path).stem for media_file in media_files}

    # First pass: exact filename match
    for subtitle in subtitle_files:
        for media_file, base_name in media_base_names.items():
            # If the subtitle's media name matches the base name of the media file
            if subtitle.media_name == base_name:
                matches[media_file].append(subtitle)

    # Second pass: check for partial matches for remaining unmatched subtitles
    unmatched_subtitles = [
        sub for sub in subtitle_files if not any(sub in matched for matched in matches.values())
    ]

    for subtitle in unmatched_subtitles:
        # Find best match based on media name
        best_match = None
        highest_similarity = 0

        for media_file, base_name in media_base_names.items():
            # Simple similarity check: how much of subtitle media name is in the base name
            # Could be enhanced with more sophisticated similarity metrics
            if subtitle.media_name in base_name or base_name in subtitle.media_name:
                similarity = len(set(subtitle.media_name) & set(base_name)) / len(
                    set(subtitle.media_name) | set(base_name)
                )
                if similarity > highest_similarity:
                    highest_similarity = similarity
                    best_match = media_file

        # If we found a match with sufficient similarity, add it
        if best_match and highest_similarity > 0.5:  # Configurable threshold
            matches[best_match].append(subtitle)

    return matches


def generate_subtitle_filename(
    media_filename: str,
    language: str = "en",
    forced: bool = False,
    sdh: bool = False,
    extension: str = ".srt",
) -> str:
    """Generate a standardized subtitle filename based on a media filename.

    Args:
        media_filename: The media file name to base the subtitle name on
        language: Language code for the subtitle (default: "en")
        forced: Whether this is a forced subtitle (default: False)
        sdh: Whether this is an SDH subtitle (default: False)
        extension: The subtitle file extension (default: ".srt")

    Returns:
        A standardized subtitle filename
    """
    # Extract the base name without extension
    from pathlib import Path

    base_name = Path(media_filename).stem

    # Build the components of the subtitle filename
    components = [base_name, language]

    # Add flags if needed
    if forced:
        components.append("forced")
    if sdh:
        components.append("sdh")

    # Ensure extension starts with a dot
    if not extension.startswith("."):
        extension = f".{extension}"

    # Join the components with dots and add the extension
    return f"{'.'.join(components)}{extension}"
