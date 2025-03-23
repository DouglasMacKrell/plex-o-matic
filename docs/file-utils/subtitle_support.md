# Subtitle Support

Plex-o-matic provides comprehensive support for managing subtitle files alongside your media. This feature ensures that subtitle files are properly named and organized according to Plex conventions, making them automatically available in your Plex library.

## Features

- Detection of common subtitle file formats (`.srt`, `.sub`, `.vtt`, `.ass`, `.ssa`)
- Automatic language detection from filenames
- Support for "forced" and "SDH" (Subtitles for the Deaf and Hard of hearing) subtitle types
- Matching subtitle files to their corresponding media
- Renaming subtitle files to follow Plex naming conventions
- Moving subtitle files alongside their media files during organization

## Subtitle File Naming Convention

Plex uses a specific naming convention for subtitle files to automatically detect language and type:

```
MovieName.en.srt        # English subtitle
MovieName.fr.srt        # French subtitle
MovieName.en.forced.srt # Forced English subtitle
MovieName.en.sdh.srt    # English subtitle for the deaf and hard of hearing
```

Plex-o-matic automatically generates these standardized names to ensure maximum compatibility.

## How Subtitle Matching Works

When Plex-o-matic scans a directory, it identifies both media files and subtitle files. It then uses a two-step matching process:

1. **Exact matching**: Subtitle files with names that directly match their media counterparts (minus language and type tags) are paired together.
2. **Fuzzy matching**: For remaining subtitle files, a similarity algorithm is used to find the best media file match.

## Configuration

Subtitle support is enabled by default. You can customize it in your configuration:

```json
{
    "subtitle_extensions": [".srt", ".sub", ".vtt", ".ass", ".ssa"],
    "subtitle_handling": {
        "enabled": true,
        "auto_match": true,
        "default_language": "en",
        "rename_with_media": true
    }
}
```

## Usage Examples

### Listing Subtitle Files

To see what subtitle files will be processed during a scan:

```bash
plexomatic scan --path /your/media/path --show-subtitles
```

### Renaming Without Moving

To rename subtitle files to follow Plex conventions without moving them:

```bash
plexomatic rename --subtitles-only --path /your/media/path
```

### Preview Subtitle Changes

Before applying changes, preview how subtitle files will be renamed:

```bash
plexomatic preview --path /your/media/path
```

## SubtitleFile Class

For developers, Plex-o-matic provides a `SubtitleFile` class to represent subtitle files:

```python
from plexomatic.core.subtitle_scanner import SubtitleFile

# Create a subtitle file instance
subtitle = SubtitleFile(Path("movie.en.srt"))

# Access properties
print(subtitle.language)  # "en"
print(subtitle.is_forced)  # False
print(subtitle.is_sdh)    # False
print(subtitle.media_name)  # "movie"
```

## Scanning and Matching

The `subtitle_scanner` module provides functions for scanning directories and matching subtitles to media:

```python
from plexomatic.core.subtitle_scanner import scan_for_subtitles, match_subtitles_to_media
from plexomatic.core.file_scanner import FileScanner

# Scan for media files
scanner = FileScanner("/path/to/media")
media_files = list(scanner.scan())

# Scan for subtitle files
subtitle_extensions = [".srt", ".sub", ".vtt", ".ass", ".ssa"]
subtitle_files = scan_for_subtitles("/path/to/media", subtitle_extensions)

# Match subtitles to media
matches = match_subtitles_to_media(media_files, subtitle_files)

# Process matches
for media_file, subtitles in matches.items():
    print(f"Media: {media_file.path.name}")
    for subtitle in subtitles:
        print(f"  Subtitle: {subtitle.path.name} ({subtitle.language})")
```

## Generating Subtitle Filenames

To generate a standardized subtitle filename:

```python
from plexomatic.core.subtitle_scanner import generate_subtitle_filename

# Generate a standard subtitle filename
filename = generate_subtitle_filename(
    "Movie.2020.mp4",  # Media filename
    language="en",     # Language code
    forced=False,      # Is it a forced subtitle?
    sdh=True,          # Is it an SDH subtitle?
    extension=".srt"   # Subtitle extension
)
# Returns: "Movie.2020.en.sdh.srt"
```
