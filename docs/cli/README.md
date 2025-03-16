# Plex-o-matic CLI Documentation

Plex-o-matic provides a powerful command-line interface (CLI) to help you organize your media files for Plex.

## Installation

The CLI is included when you install Plex-o-matic:

```bash
pip install plex-o-matic
```

After installation, you can access the CLI using the `plexomatic` command.

## Available Commands

### Main CLI

```bash
plexomatic [OPTIONS] COMMAND [ARGS]...
```

**Options:**
- `--version`: Show the current version of Plex-o-matic.
- `--verbose, -v`: Enable verbose output for more detailed information.
- `--help`: Show help message and exit.

### Scan Command

Scan media directories for files to organize.

```bash
plexomatic scan [OPTIONS]
```

**Options:**
- `--path, -p PATH`: Path to directory containing media files (required).
- `--recursive/--no-recursive`: Scan directories recursively (default: recursive).
- `--extensions, -e TEXT`: Comma-separated list of file extensions to scan (default: .mp4,.mkv,.avi,.mov,.m4v).
- `--verbose, -v`: Enable verbose output.
- `--help`: Show help message and exit.

**Example:**
```bash
plexomatic scan --path /media/tv_shows --extensions .mp4,.mkv --verbose
```

### Preview Command

Preview changes that would be made to your media files without actually making any changes.

```bash
plexomatic preview [OPTIONS]
```

**Options:**
- `--verbose, -v`: Enable verbose output.
- `--help`: Show help message and exit.

**Example:**
```bash
plexomatic preview --verbose
```

### Apply Command

Apply the planned changes to your media files.

```bash
plexomatic apply [OPTIONS]
```

**Options:**
- `--dry-run`: Show what would be done without making changes.
- `--verbose, -v`: Enable verbose output.
- `--help`: Show help message and exit.

**Example:**
```bash
plexomatic apply --dry-run
```

### Rollback Command

Rollback the last operation or a specific operation by ID.

```bash
plexomatic rollback [OPTIONS]
```

**Options:**
- `--operation-id INTEGER`: ID of the operation to roll back (defaults to last operation).
- `--verbose, -v`: Enable verbose output.
- `--help`: Show help message and exit.

**Example:**
```bash
plexomatic rollback --operation-id 42
```

## Workflow Examples

### Basic Media Scan and Organization

```bash
# Scan your media directory
plexomatic scan --path /media/tv_shows

# Preview changes that would be made
plexomatic preview

# Apply the changes if the preview looks good
plexomatic apply

# If something goes wrong, rollback the changes
plexomatic rollback
```

### Advanced Usage with Verbose Output

```bash
# Scan with verbose output and limited extensions
plexomatic scan --path /media/movies --extensions .mp4,.mkv --verbose

# Apply changes with a dry run first
plexomatic apply --dry-run --verbose

# Then apply for real
plexomatic apply
```

## Environment Variables

Plex-o-matic CLI also respects the following environment variables:

- `PLEXOMATIC_CONFIG_PATH`: Path to a custom configuration file
- `PLEXOMATIC_LOG_LEVEL`: Set logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

## Exit Codes

The CLI uses the following exit codes:

- `0`: Command completed successfully
- `1`: General error
- `2`: Invalid command line options
- `3`: Media file scanning error
- `4`: Operation application error
- `5`: Rollback error 