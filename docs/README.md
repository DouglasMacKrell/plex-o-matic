![Plex-O-Matic Title Image](../public/Plex-O-Matic_README_Title_Image.webp)

# Plex-o-matic Documentation

Welcome to the Plex-o-matic documentation. This guide will help you understand how to use and get the most out of Plex-o-matic for organizing your media files.

## Table of Contents

- [Getting Started](#getting-started)
- [Usage Guide](#usage-guide)
- [Documentation Sections](#documentation-sections)
- [FAQs](#faqs)

## Getting Started

Plex-o-matic is a powerful tool designed to help you organize your media files for Plex. It automates the process of scanning, renaming, and organizing media files according to Plex's preferred naming conventions.

**New users**: Check out our comprehensive [Getting Started Guide](getting_started.md) for step-by-step instructions on installation, configuration, and your first media organization workflow.

### Installation

#### From Source

1. Clone the repository:
```bash
git clone https://github.com/DouglasMacKrell/plex-o-matic.git
cd plex-o-matic
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -e .
```

#### From PyPI

```bash
pip install plex-o-matic
```

## Usage Guide

Once installed, you can use Plex-o-matic via the command line interface:

```bash
# Set up your API keys and configuration
plexomatic configure

# Scan your media directory
plexomatic scan --path /path/to/your/media

# Preview changes that would be made
plexomatic preview

# Apply the changes if they look good
plexomatic apply

# If something goes wrong, rollback
plexomatic rollback
```

For more detailed usage instructions, please refer to the [CLI Documentation](cli/README.md).

## Documentation Sections

- [CLI Documentation](cli/README.md): Detailed information on using the command line interface.
- [Configuration System](configuration/README.md): Information about configuring Plex-o-matic.
- [File Utilities](file-utils/README.md): Documentation on filename standardization and file operations.
  - [Template System](file-utils/template_system.md): Information about the template system for customizing file names.
  - [Subtitle Support](file-utils/subtitle_support.md): Information about subtitle support.
- [Backend Architecture](backend/README.md): Information about the backend design and components.
  - [MediaType System](backend/media_type.md): Documentation on the MediaType enum consolidation and compatibility layers.
- [Database Schema](database/README.md): Documentation on the database structure and schema.
- [API Integration](api/README.md): Documentation on API clients and integration.
- [Metadata Management](metadata/README.md): Information about the metadata management system.
- [Episode Handling](episode_handling.md): TV show episode handling features.
- [Metadata-Episode Integration](metadata/episode_integration.md): Integration between metadata system and episode handling.

## Features

Plex-o-matic provides several powerful features:

### Media File Scanning
- Recursive directory scanning
- Configurable file extensions
- Ignore patterns for samples and extras

### Filename Standardization
- TV show filename detection and standardization
- Movie filename detection and standardization
- Multi-episode detection
- Special episode handling (TV specials, OVAs)
- Anime-specific naming conventions
- Proper Plex-compatible naming

### Media Type Detection
- **TV_SHOW**: Regular TV show episodes
- **MOVIE**: Movie files
- **ANIME**: Anime TV series episodes
- **TV_SPECIAL**: Special episodes, OVAs, extras, and behind-the-scenes content
- **ANIME_SPECIAL**: Anime specials, OVAs, and movies tied to a series

### Safe File Operations
- Backup system with SQLite integration
- Checksum verification
- Operation rollback capability

### Configuration System
- JSON-based configuration
- Environment variable support
- Extensible options
- Interactive configuration via CLI

### Media Management
- Automated media file detection and scanning
- Recursive directory traversal
- Customizable file types and ignore patterns
- Subtitle file detection and management
- Language and format detection for subtitles

## FAQs

### How does Plex-o-matic handle existing files?

Plex-o-matic uses a backup system to keep track of all file operations. This ensures that any changes made can be rolled back if needed. Each operation is recorded in a SQLite database with checksums for verification.

### Can I use Plex-o-matic with existing Plex installations?

Yes, Plex-o-matic is designed to work with existing Plex installations and follows Plex's naming conventions. It doesn't modify your Plex database, only the files themselves.

### How do I customize the file extensions that are processed?

You can configure the allowed file extensions in the configuration file (`~/.plexomatic/config.json`) or by using the `--extensions` option in the CLI:

```bash
plexomatic scan --path /media --extensions .mp4,.mkv
```

### Can I preview changes before applying them?

Yes, you can use the `preview` command to see what changes would be made without actually making any changes:

```bash
plexomatic preview --path /media
```

### How do I rollback changes if something goes wrong?

You can use the `rollback` command to undo the last operation:

```bash
plexomatic rollback
```

Or specify a specific operation ID:

```bash
plexomatic rollback --operation-id 42
```

### How do I set up API keys for metadata sources?

You can use the interactive configuration command:

```bash
plexomatic configure
```

This will guide you through setting up API keys for TVDB, TMDB, and other metadata sources. It's the recommended way to configure Plex-o-matic rather than editing the configuration file manually.

### How does Plex-o-matic handle special episodes like OVAs and extras?

Plex-o-matic has dedicated media types for special episodes:

- **TV_SPECIAL**: For TV show specials, extras, OVAs, behind-the-scenes content
- **ANIME_SPECIAL**: For anime specials, OVAs, and movies related to a series

The system automatically detects these special types and organizes them according to Plex's conventions (typically in Season 0). For more details, see the [Episode Handling](episode_handling.md) documentation.
