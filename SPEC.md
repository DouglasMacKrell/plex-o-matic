# Plex-o-matic

## Overview
Plex-o-matic is an intelligent media file organization tool designed to automate the process of renaming and structuring media files for optimal Plex compatibility. It handles complex scenarios such as multi-episode files, series name verification, and maintains a safety system for all operations.

## Core Features

### 1. File Management
- Scan and analyze media directories
- Rename files according to Plex naming conventions
- Handle multi-episode file naming
- Maintain directory structure according to Plex requirements
- Support for TV Shows, Movies, and Music

### 2. Metadata Integration
- TVDB API integration for TV show verification
- TMDB API integration for movie verification
- Local LLM integration for complex name parsing
- Confidence scoring for matches

### 3. Safety Systems
- Database-backed rename history
- Rollback capability for any rename operation
- Preview system for pre-verification
- Checksum verification for file integrity
- Detailed logging of all operations

### 4. Special Handling
- Multi-episode concatenation
- Season pack organization
- Music album structure
- Subtitle file matching
- Extra features and behind-the-scenes content

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

## User Interface
- Command Line Interface (CLI)
- Configuration via YAML
- Interactive preview system
- Batch operation support

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