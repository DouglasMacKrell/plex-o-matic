![Plex-O-Matic Title Image](public/Plex-O-Matic_README_Title_Image.webp)

# Plex-o-matic

## Overview
Plex-o-matic is an intelligent media file organization tool designed to automate the process of renaming and structuring media files for optimal Plex compatibility. It handles complex scenarios such as multi-episode files, series name verification, and maintains a safety system for all operations.

## Primary Purpose
Plex-o-matic's primary goal is to transform existing media files with potentially inconsistent naming into a format that Plex's metadata agents can properly identify and match. The application analyzes file names, determines the media type, and then uses specialized APIs to verify and enhance the metadata before generating a properly formatted file name following Plex's naming conventions.

## Media Identification and Formatting Workflow
1. **Initial Filename Analysis**
   - Parse the filename using regex patterns
   - Extract potential show name, season/episode numbers, year, and other identifiers
   - Make preliminary media type determination (TV, Movie, Anime, Music)

2. **Media Type Verification**
   - **Multi-Stage Detection Process**:
     1. Initial pattern-based analysis of filename and path
     2. API verification of detected media type candidates
     3. Confidence scoring for each potential media type
     4. LLM assistance for cases below confidence threshold
   - **Pattern-Based Detection**:
     - TV Show patterns (S01E01, 1x01, etc.)
     - Movie patterns (Title (Year), etc.)
     - Anime-specific patterns
     - Music patterns (Artist - Album - Track, etc.)
     - Path structure indicators (folders named "Season XX")
   - **API Verification**:
     - TMDB search for movie candidates
     - TVDB search for TV show candidates
     - AniDB search for anime candidates
     - MusicBrainz search for music candidates
     - Compare API results against extracted metadata
     - Calculate match confidence based on returned results
   - **LLM Assistance**:
     - Provide extracted metadata and API results to LLM
     - Ask LLM to determine most likely media type
     - Use LLM to clean and normalize extracted metadata
     - Generate search queries for APIs when direct matches fail
     - Provide reasoning for media type determination
   - **Confidence Scoring**:
     - Combined score from pattern matching, API results, and LLM input
     - Threshold settings for automatic vs. manual handling
     - Weighting factors for different verification methods
     - Special case handling for known edge cases
   - **Fallback Strategy**:
     - Attempt multiple API searches with variations of the name
     - Try alternative media types when primary type has low confidence
     - Present multiple options to user when confidence is below threshold
     - Use file characteristics (duration, size, etc.) as additional signals

3. **Metadata Enhancement**
   - Fetch rich metadata from appropriate APIs based on verified media type
   - Correct show/movie titles, episode names, etc.
   - Handle special cases like anthology shows, multi-episode files
   - Apply language and region specific fixes
   - Use LLM to connect ambiguous file names to correct metadata
   - Fill in missing metadata details from the most reliable sources

4. **Plex-Compatible Filename Generation**
   - Format files according to Plex naming conventions based on media type
   - Ensure proper organization into Plex's expected directory structure
   - Handle special formatting for multi-episode files, specials, etc.
   - Validate generated filenames against Plex requirements
   - Format filenames to match exactly what Plex metadata agents expect

5. **Preview and Execution**
   - Show before/after comparison
   - Provide confidence ratings for each rename operation
   - Allow user confirmation before changes
   - Execute rename operations with full backup capabilities
   - Log all operations for future reference or rollback

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

### 1. Media Type Detection and Verification
- Multi-stage detection pipeline:
  1. Initial pattern-based detection from filenames
  2. API verification when pattern detection is uncertain
  3. LLM assistance for highly ambiguous cases
- Confidence scoring for each detection method
- Fallback strategies for uncertain cases
- Support for TV Shows, Movies, Anime, and Music
- Detailed logging of detection steps

### 2. API Integration for Metadata Verification and Enhancement
- **TMDB Client** (movies and some TV shows)
  - Primary source for movie metadata
  - Alternative source for TV show metadata
  - Title verification and correction
  - Year verification
  - Genre and content information
- **TVDB Client** (TV shows)
  - Primary source for TV show metadata
  - Series name verification
  - Season and episode verification
  - Episode title lookup
  - Handles special episodes and season ordering
- **AniDB Client** (anime specific)
  - Specialized handling for anime naming conventions
  - Season order verification (often different from western shows)
  - Episode title and numbering verification
  - Character and staff information
- **TVMaze Client** (additional TV data)
  - Alternative season/episode ordering
  - Network information
  - Air dates and production details
  - Cast information
- **MusicBrainz Client** (music files)
  - Artist verification and correction
  - Album and track information
  - Release year verification
  - Genre and style information
  - MusicBrainz ID (MBID) utilization for precise matching
  - Release group identification
  - Artist relationships and collaborations
  - Track listing and duration verification
  - Support for various music release types (album, single, EP, compilation)
- **LLM Integration** (ambiguity resolution)
  - Connect ambiguous file names to correct metadata
  - Extract segments from anthology episodes
  - Resolve conflicts between different metadata sources
  - Generate missing metadata when APIs fail
  - Parse complex or non-standard filenames

### 3. File Management
- Scan and analyze media directories
- Rename files according to Plex naming conventions
- Handle multi-episode file naming
- Maintain directory structure according to Plex requirements
- Support for TV Shows, Movies, Anime, and Music
- Anthology mode for multi-segment episodes
- Title-based episode matching
- Directory structure inference
- Subtitle file detection and management
  - Support for common subtitle formats (.srt, .sub, .vtt, .ass, .ssa)
  - Automatic language detection from filenames
  - Handling for "forced" and "SDH" subtitle types
  - Matching subtitles to media files
  - Standardized Plex-compatible subtitle naming

### 4. Metadata Integration
- **API Client Integration**
  - Unified interface for multiple metadata sources
  - Comprehensive error handling and rate limiting
  - Caching system to minimize API calls
  - Fallback strategies when primary APIs are unavailable
- **Metadata Aggregation**
  - Weighted scoring for conflicting metadata
  - Merging data from multiple sources
  - Priority system for preferred metadata sources
  - Custom rules for specific media types or shows
- **Confidence System**
  - Scoring for each metadata element
  - Overall match confidence calculation
  - Threshold settings for automatic vs. manual handling
  - User override capabilities for uncertain matches

### 5. Safety Systems
- Backup system for all file operations
- Operation tracking with SQLite database
- Rollback capability for any operation
- File checksum verification for integrity
- Preview mode for seeing changes before applying
- Confirmation prompts for sensitive operations
- Support for dry run mode in all commands
- Comprehensive logging of all operations

### 6. Quality Assurance
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

### 7. Special Handling
- Multi-episode concatenation
- Season pack organization
- Special episode handling (OVAs, specials)
- Anthology show support
- Title-based episode matching for complex scenarios
- Directory structure inference for better organization

### 8. User Interface
- Command Line Interface (CLI)
- Interactive configuration wizard
- Batch operations for efficiency
- Progress indicators for long operations
- Verbose output mode for diagnostics
- Color coding for better readability
- Interactive mode for complex operations

### 9. Preview System
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

### 10. Subtitle Support
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

### 2. Code Architecture and Modularity
- **Clean Module Organization**:
  - Limited module sizes (<500 lines where possible)
  - Single responsibility principle for modules and classes
  - Proper separation of concerns
  - Limited public interfaces for each module
- **Functional Areas**:
  - Parsing: Extract information from filenames and paths
  - Formatting: Generate formatted filenames based on metadata
  - API Integration: Interface with external APIs
  - Processing: Orchestrate the workflow from parsing to output
  - CLI: User interface and command handling
- **Common Patterns**:
  - Factory patterns for media type handling
  - Strategy patterns for different formatting styles
  - Repository pattern for persistent data access
  - Dependency injection for better testability
  - Observer pattern for event handling
- **Project Structure**:
  - Core domain modules in domain/
  - API clients in api/
  - Utility functions in utils/
  - CLI interface in cli/
  - Configuration in config/
  - Testing in tests/ mirroring project structure

### 3. API Integration
- TVDB API for TV show data
- TMDB API for movie data
- AniDB UDP/HTTP API for anime data
- TVMaze API for additional TV data
- Local LLM integration for complex scenarios

### 4. File System Operations
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

## Media Type Specific Processing

### TV Shows
1. Extract show name, season, and episode numbers from filename
2. Verify show name against TVDB and TMDB
3. Correct season and episode numbers if needed
4. Fetch episode titles and additional metadata
5. Format filename according to Plex TV show conventions
6. Place in correct directory structure

### Movies
1. Extract movie title and year from filename
2. Verify against TMDB
3. Correct title and year if needed
4. Format filename according to Plex movie conventions
5. Place in correct directory structure with year in folder name

### Anime
1. Extract show name, season, and episode information
2. Special handling for alternative episode ordering
3. Verify against AniDB
4. Handle specials, OVAs, and movies appropriately
5. Format according to Plex anime conventions

### Music
1. Extract artist, album, and track information from filename and path
2. Verify artist name against MusicBrainz
   - Handle various artist name formats (featuring artists, collaborations)
   - Correct misspellings or alternative spellings
   - Identify artist MusicBrainz ID (MBID) for precise matching
3. Verify album information
   - Match against MusicBrainz release database
   - Determine correct release year
   - Identify album type (studio album, live, compilation, etc.)
   - Handle multiple versions of same album (deluxe, remaster, etc.)
4. Process track data
   - Verify track number and disc number
   - Correct track title formatting
   - Handle featured artists in track titles
   - Identify multi-part tracks
5. Format according to Plex music conventions
   - Artist/Album/Track structure with proper capitalization
   - Include release year in album folder name when available
   - Format track numbers with leading zeros
   - Handle various artist scenarios (compilations, soundtracks, etc.)
6. Organize into artist/album directory structure
   - Create proper folder hierarchy
   - Handle "Various Artists" compilations
   - Properly format soundtrack albums
   - Support classical music naming (composer vs. performer)

### Anthology Shows
1. Detect anthology episodes based on patterns or specified shows
2. Extract segment titles using LLM assistance
3. Determine episode range based on number of segments
4. Format with appropriate episode range (S01E01-E03)
5. Include segment titles in combined format

## File Naming Conventions

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
