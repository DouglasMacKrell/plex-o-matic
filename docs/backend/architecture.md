# Backend Architecture

## Overview

The Plex-o-matic backend is designed with a modular architecture that separates concerns and provides clear interfaces between components. The system is built to be reliable, maintainable, and safe when handling file operations.

## Core Components

### 1. File Scanner (`plexomatic.core.file_scanner`)

The file scanner module is responsible for discovering and analyzing media files in the filesystem.

#### Key Classes:
- `FileScanner`: Main class for scanning directories
  - Handles recursive directory traversal
  - Filters files based on extensions and patterns
  - Identifies media files and their properties

- `MediaFile`: Represents a media file with its properties
  - Basic file information (path, size, extension)
  - Media-specific properties (multi-episode detection)

#### Usage Example:
```python
scanner = FileScanner(
    base_path="/media/tv_shows",
    allowed_extensions=[".mp4", ".mkv", ".avi"],
    ignore_patterns=[r"^\.", r"Thumbs\.db$"]
)

for media_file in scanner.scan():
    print(f"Found: {media_file.path}")
```

### 2. Backup System (`plexomatic.core.backup_system`)

The backup system provides safe file operations with rollback capability.

#### Key Classes:
- `BackupSystem`: Manages file operations and their history
  - Records file operations in SQLite database
  - Provides operation status tracking
  - Enables safe rollback of operations

- `FileOperation`: Data class for file operations
  - Stores operation details (paths, type, checksum)
  - Used for operation recording and verification

#### Usage Example:
```python
backup = BackupSystem(db_path="~/.plexomatic/operations.db")
operation = FileOperation(
    original_path="/path/old.mp4",
    new_path="/path/new.mp4",
    operation_type="rename",
    checksum="abc123"
)

# Record and perform operation
op_id = backup.record_operation(operation)
# ... perform actual file operation ...
backup.mark_operation_complete(op_id)

# Rollback if needed
backup.rollback_operation(op_id)
```

## Operation Flow

1. **File Discovery**
   - File Scanner traverses specified directories
   - Identifies media files and their properties
   - Filters out system files and non-media content

2. **Operation Planning**
   - Analyze file names and structure
   - Determine necessary operations
   - Generate new file names/paths

3. **Safe Execution**
   - Record operations in backup system
   - Perform file operations
   - Track operation status
   - Enable rollback if needed

## Error Handling

- All file operations are tracked in the database
- Operations can be rolled back individually
- Checksums verify file integrity
- Detailed error logging and status tracking

## Future Extensions

1. **Planned Features**
   - Batch operation support
   - Operation preview system
   - Advanced media analysis
   - Parallel processing

2. **Integration Points**
   - TVDB/TMDB API integration
   - Local LLM integration
   - Plex API integration
