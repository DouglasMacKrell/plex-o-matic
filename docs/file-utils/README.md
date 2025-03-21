![Plex-O-Matic Title Image](../../public/Plex-O-Matic_README_Title_Image.webp)

# File Utilities

Plex-o-matic includes powerful utilities for handling file operations and standardizing media filenames.

## Name Utilities

The name utilities help standardize media filenames according to Plex's preferred naming conventions.

### File Name Detection

The system can detect common patterns in media filenames:

- **TV Show Pattern**: `ShowName.S01E02.EpisodeTitle.ext`
- **Movie Pattern**: `MovieName.2020.OptionalInfo.ext`

Example:

```python
from plexomatic.utils import extract_show_info

# TV Show example
info = extract_show_info("The.Office.S03E05.Episode.Title.mp4")
# Returns: {'show_name': 'The Office', 'season': '03', 'episode': '05', 'title': 'Episode.Title'}

# Movie example
info = extract_show_info("Inception.2010.1080p.mp4")
# Returns: {'movie_name': 'Inception', 'year': '2010', 'info': '1080p'}
```

### Filename Generation

You can generate standardized filenames for TV shows and movies:

```python
from plexomatic.utils import generate_tv_filename, generate_movie_filename

# Generate TV show filename
tv_filename = generate_tv_filename("The Office", 3, 5, "Business School", ".mp4")
# Returns: "The.Office.S03E05.Business.School.mp4"

# Generate movie filename
movie_filename = generate_movie_filename("Inception", 2010, ".mp4")
# Returns: "Inception.2010.mp4"
```

### Filename Sanitization

The `sanitize_filename` function ensures that filenames don't contain invalid characters:

```python
from plexomatic.utils import sanitize_filename

safe_name = sanitize_filename("File: with invalid? chars")
# Returns: "File_ with invalid_ chars"
```

### Preview Rename

Before renaming files, you can preview the changes:

```python
from pathlib import Path
from plexomatic.utils import get_preview_rename

original_path = Path("/media/tv/The Office S3E5 Business School.mp4")
original, new = get_preview_rename(original_path)

if new:
    print(f"Would rename: {original.name} → {new.name}")
```

## File Operations

Plex-o-matic provides file operations with built-in backup functionality.

### Safe File Renaming

The `rename_file` function safely renames files with backup support:

```python
from pathlib import Path
from plexomatic.utils import rename_file
from plexomatic.core.backup_system import BackupSystem

# Initialize backup system
backup_system = BackupSystem(Path("~/.plexomatic/plexomatic.db").expanduser())
backup_system.initialize_database()

# Rename a file with backup
success = rename_file(
    Path("/media/tv/The Office S3E5.mp4"),
    Path("/media/tv/The.Office.S03E05.mp4"),
    backup_system
)
```

### Checksums

File operations use checksums to verify integrity:

```python
from plexomatic.utils import calculate_file_checksum

checksum = calculate_file_checksum(Path("file.mp4"))
```

### Rollback Operations

You can roll back file operations:

```python
from plexomatic.utils import rollback_operation

# Rollback operation by ID
success = rollback_operation(operation_id=42, backup_system=backup_system)
```

## Using with the CLI

The CLI commands for preview, apply, and rollback use these utilities:

```bash
# Preview changes
plexomatic preview --path /media/tv_shows

# Apply changes
plexomatic apply --path /media/tv_shows

# Rollback
plexomatic rollback
```
