![Plex-O-Matic Title Image](public/Plex-O-Matic_README_Title_Image.webp)

# Plex-o-matic

## Overview
Plex-o-matic is an intelligent media file organization tool designed to automate the process of renaming and structuring media files for optimal Plex compatibility. It handles complex scenarios such as multi-episode files, series name verification, and maintains a safety system for all operations.

## Installation

Plex-o-matic is available on PyPI and can be installed with pip:

```bash
pip install plex-o-matic
```

For development or the latest features, you can install from source:

```bash
git clone https://github.com/DouglasMacKrell/plex-o-matic.git
cd plex-o-matic
pip install -e .
```

## Core Features

### 1. File Management
- Scan and analyze media directories
- Rename files according to Plex naming conventions
- Handle multi-episode file naming
- Maintain directory structure according to Plex requirements
- Support for TV Shows, Movies, and Music
- Anthology mode for multi-segment episodes
- Title-based episode matching
- Directory structure inference
- Subtitle file detection and management
  - Support for common subtitle formats (.srt, .sub, .vtt, .ass, .ssa)
  - Automatic language detection from filenames
  - Handling for "forced" and "SDH" subtitle types
  - Matching subtitles to media files
  - Standardized Plex-compatible subtitle naming

### 2. Metadata Integration
- TVDB API integration for TV show verification
- TMDB API integration for movie verification
- AniDB API integration for anime verification
- TVMaze API integration for additional TV data
- Local LLM integration for complex name parsing
- Metadata Manager system for aggregating multiple sources
- Unified search interface across all providers
- Confidence scoring for matches
- Customizable match threshold

### 3. Safety Systems
- Backup system for all file operations
- Operation tracking with SQLite database
- Rollback capability for any operation
- File checksum verification for integrity
- Preview mode for seeing changes before applying
- Confirmation prompts for sensitive operations
- Support for dry run mode in all commands
- Comprehensive logging of all operations

### 4. Quality Assurance
- Strict type checking with mypy
  - Comprehensive type annotations throughout codebase
  - `--disallow-untyped-defs` enforcement for test files
  - Gradual typing roadmap for continued improvement
- Comprehensive test suite
  - Unit tests for all components
  - Integration tests for complex interactions
  - Mock-based testing for external API dependencies
  - 80%+ code coverage target
  - Codecov integration for coverage reporting and tracking
- Code quality tools
  - Black for code formatting
  - Ruff for linting and static analysis
  - Pre-commit hooks for automated checks
  - Continuous integration with GitHub Actions

### 5. Special Handling
- Multi-episode concatenation
- Season pack organization
- Special episode handling (OVAs, specials)
- Anthology show support
- Title-based episode matching for complex scenarios
- Directory structure inference for better organization

### 6. User Interface
- Command Line Interface (CLI)
- Interactive configuration wizard
- Batch operations for efficiency
- Progress indicators for long operations
- Verbose output mode for diagnostics
- Color coding for better readability
- Interactive mode for complex operations

### 7. Preview System
- Advanced diff display for file operations
  - Side-by-side comparison of original and new filenames
  - Highlighting of changes in filenames
  - Color-coded diff output for clarity
- Batch preview for multiple files
  - Tabular format for large numbers of files
  - Grouping of similar operations
  - Sorting and filtering options
- Interactive approval process
  - Per-file approval option
  - Batch approval for similar changes
  - Skip/ignore functionality for specific files
  - Edit suggestions before applying
- Preview persistence
  - Save preview results for later review
  - Export preview as JSON or CSV
  - Resume previously saved preview session

### 8. Subtitle Support
- Subtitle file detection and scanning
  - Configurable subtitle file extensions
  - Automatic recursive scanning
  - Integration with existing file scanning system
- Language and format detection
  - Automatic language code identification (en, fr, de, etc.)
  - Detection of forced subtitles for foreign language parts
  - Support for SDH (Subtitles for the Deaf and Hard of hearing)
- Subtitle-to-media matching
  - Exact filename matching algorithm
  - Fuzzy matching for unmatched subtitles
  - Similarity scoring system
  - Confidence thresholds for matches
- Plex-compatible renaming
  - Standardized naming convention (MovieName.en.srt)
  - Proper language code handling
  - Support for forced and SDH flags in filenames
  - Preservation of original language when renaming
- Preview and organization
  - Subtitle operations shown in preview system
  - Batch handling of subtitles with media
  - Detailed logging of subtitle operations
  - Interactive approval for subtitle changes

## Configuration Options

### Subtitle Handling
- `subtitle_extensions`: List of subtitle file extensions to process
- `subtitle_handling.enabled`: Master toggle for subtitle handling
- `subtitle_handling.auto_match`: Enable automatic subtitle matching
- `subtitle_handling.default_language`: Default language code for unspecified subtitles
- `subtitle_handling.rename_with_media`: Whether to rename subtitles when media is renamed

### Anthology Mode
- `anthology_mode`: Enable special handling for anthology shows
- `title_match_priority`: Weight for title vs episode number matching
- `infer_from_directory`: Enable series name inference from directory structure
- `match_threshold`: Confidence threshold for title matching

### Preview System Options
- `diff_style`: Style for diff display (side-by-side, unified, or minimal)
- `color_mode`: Enable/disable colored output
- `batch_size`: Number of files to display at once in batch mode
- `interactive_default`: Default action for interactive prompts
- `preview_format`: Format for exporting previews (JSON, CSV, text)

## Technical Specifications

### 1. Language and Dependencies
- Python 3.8+
- SQLite for database storage
- SQLAlchemy for ORM
- Requests for API interaction
- Click for CLI interface
- Pyyaml for configuration

### 2. API Integration
- TVDB API for TV show data
- TMDB API for movie data
- AniDB UDP/HTTP API for anime data
- TVMaze API for additional TV data
- Local LLM integration for complex scenarios

### 3. File System Operations
- Safe file rename operations
- Directory creation and management
- File checksum verification
- File backup and restore

## Technical Requirements

### System Requirements
- Python 3.8+
- SQLite3
- Local LLM system
- Internet connection for API access

### External Dependencies
- TVDB API access
- TMDB API access
- Local LLM API

### File Naming Conventions

#### TV Shows
Input Example:
```
Daniel Tiger S Neighborhood-S01E01-Daniel S Birthday Daniel S Picnic.mp4
```
Output Example:
```
Daniel Tiger's Neighborhood - S01E01-E02 - Daniel's Birthday & Daniel's Picnic.mp4
```

Directory Structure:
```
TV Shows/
└── Show Name/
    └── Season XX/
        └── Show Name - SXXEXX - Episode Name.ext
```

#### Movies
```
Movies/
└── Movie Name (Year)/
    └── Movie Name (Year).ext
```

#### Music
```
Music/
└── Artist/
    └── Album (Year)/
        └── XX - Track Name.ext
```

## Safety Features

### Backup System
- SQLite database for rename tracking
- Original filename preservation
- Timestamp tracking
- File checksum verification
- Operation status tracking

### Database Schema
```sql
CREATE TABLE file_renames (
    id INTEGER PRIMARY KEY,
    original_path TEXT,
    original_name TEXT,
    new_name TEXT,
    renamed_at TIMESTAMP,
    media_type TEXT,
    checksum TEXT,
    status TEXT
);
```

## Error Handling
- Detailed error messages
- Operation logging
- Automatic rollback on failure
- Conflict resolution system

## Performance Considerations
- Batch processing capability
- Efficient API usage
- Local caching of API responses
- Parallel processing where applicable

## Security
- API key management
- Backup database encryption
- Restricted file permissions
- Safe file operation practices

## Future Expansion
- Web interface
- Network share support
- Remote operation capability
- Plugin system
- Additional metadata sources
- Custom naming templates
