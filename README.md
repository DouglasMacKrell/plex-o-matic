![Plex-O-Matic Title Image](public/Plex-O-Matic_README_Title_Image.webp)

# Plex-o-matic

[![Test & Quality Check](https://github.com/DouglasMacKrell/plex-o-matic/actions/workflows/test.yml/badge.svg)](https://github.com/DouglasMacKrell/plex-o-matic/actions/workflows/test.yml)
[![codecov](https://codecov.io/gh/DouglasMacKrell/plex-o-matic/branch/main/graph/badge.svg)](https://codecov.io/gh/DouglasMacKrell/plex-o-matic)

An intelligent media file organization tool for Plex that helps automate the process of renaming and structuring media files for optimal Plex compatibility.

## New to Plex-o-matic?

Check out our comprehensive [Getting Started Guide](docs/getting_started.md) for step-by-step instructions on installation, configuration, and your first media organization workflow.

## Features

- **Media File Management**:
  - Automated media file detection and scanning
  - Recursive directory traversal
  - Configurable file extensions and ignore patterns
  - Multi-episode file detection
  - Subtitle file detection and management
  - Language and format detection for subtitles

- **Smart Naming System**:
  - Automated detection of TV shows and movies
  - Plex-compatible naming conventions
  - Pattern-based filename parsing
  - Standardized output format
  - Multi-episode file detection and handling
  - Special episode detection (OVAs, specials, movies)
  - Season pack organization
  - Anthology show support with intelligent title matching
  - Directory structure inference for incomplete metadata
  - Configurable title vs. episode number priority

- **API Integration**:
  - TVDB API client for TV show metadata
  - TMDB API client for movie and TV metadata
  - AniDB API client for anime metadata
  - TVMaze API client for comprehensive TV show data
  - Local LLM integration with Ollama and Deepseek
  - Metadata-enhanced filename analysis
  - AI-powered filename suggestions

- **Metadata Management**:
  - Unified interface for all metadata sources
  - Intelligent filename matching to metadata
  - Confidence-based result ranking
  - Multi-source aggregation
  - Efficient metadata caching
  - Flexible ID format with source prefixes
  - Episode-specific metadata fetching
  - Special episode and multi-episode support
  - Metadata-driven filename generation

- **Template System**:
  - Customizable templates for TV shows, movies, and anime
  - Support for special episodes and different media types
  - Template visualization and preview functionality
  - Default templates for common naming conventions
  - Multi-episode formatting support

- **Robust Backup System**:
  - SQLite database integration for operation tracking
  - File checksum verification
  - Safe rename operations with backup/restore capability
  - Operation history with rollback support

- **User-Friendly CLI**:
  - Preview system for verifying changes before applying
  - Template management commands
  - Dry-run options for testing
  - Verbose output mode for detailed information
  - Intuitive command structure

- **Flexible Configuration**:
  - JSON-based configuration system
  - Environment variable support
  - Customizable settings for file types and naming
  - Interactive configuration wizard

## Python Compatibility

Plex-o-matic is compatible with Python 3.8-3.11. When using Python 3.8, the `typing_extensions` package is required. This dependency is automatically installed if you install the package via pip.

## Installation

### From Source

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

### From PyPI

```bash
pip install plex-o-matic
```

## Configuration

The first time you run Plex-o-matic, it will create a default configuration file at `~/.plexomatic/config.json`. You can edit this file directly or use the CLI's options to override settings.

Key configuration options:

```json
{
    "db_path": "~/.plexomatic/plexomatic.db",
    "log_level": "INFO",
    "allowed_extensions": [".mp4", ".mkv", ".avi", ".mov", ".m4v"],
    "ignore_patterns": ["sample", "trailer", "extra"],
    "recursive_scan": true,
    "backup_enabled": true,
    "api": {
        "tvdb": {
            "api_key": "",
            "auto_retry": true
        },
        "tmdb": {
            "api_key": ""
        },
        "llm": {
            "model_name": "deepseek-r1:8b",
            "base_url": "http://localhost:11434"
        }
    },
    "episode_handling": {
        "anthology_mode": false,
        "title_match_priority": 0.8,
        "infer_from_directory": true,
        "match_threshold": 0.7
    }
}
```

You can also override the configuration file location:

```bash
export PLEXOMATIC_CONFIG_PATH="/path/to/your/config.json"
```

## Basic Usage

Plex-o-matic provides a simple workflow for organizing your media files:

```bash
# Configure your API keys and settings
plexomatic configure

# Scan a directory for media files
plexomatic scan --path /path/to/media

# Preview what changes would be made
plexomatic preview

# Apply the changes
plexomatic apply

# If needed, rollback the changes
plexomatic rollback
```

### Command Options

Here are some common options that can be used with the commands:

```bash
# Scan non-recursively
plexomatic scan --path /path/to/media --no-recursive

# Scan specific file types
plexomatic scan --path /path/to/media --extensions .mp4,.mkv

# Get detailed output
plexomatic scan --path /path/to/media --verbose

# Preview all changes
plexomatic preview --path /path/to/media --verbose

# Dry run to see what would happen without making changes
plexomatic apply --dry-run

# Use anthology mode for shows with multiple episodes per file
plexomatic scan --path /path/to/anthology/show --anthology-mode
plexomatic preview --path /path/to/anthology/show --anthology-mode
plexomatic apply --path /path/to/anthology/show --anthology-mode --yes

# List all available templates
plexomatic templates list

# Show a specific template
plexomatic templates show --type TV_SHOW

# Preview a template with sample data
plexomatic templates show --type MOVIE --preview
```

For more detailed usage instructions, refer to the [documentation](docs/README.md) and the [Getting Started Guide](docs/getting_started.md).

## Development

### Setting Up Development Environment

1. Create a development environment:
```bash
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

2. Run tests:
```bash
pytest
```

3. Check code quality:
```bash
black .
ruff check .
mypy .
```

### Project Structure

- `plexomatic/`: Main package
  - `api/`: API integrations
    - `tvdb_client.py`: TVDB API client
    - `tmdb_client.py`: TMDB API client
    - `anidb_client.py`: AniDB API client
    - `tvmaze_client.py`: TVMaze API client
    - `llm_client.py`: Local LLM client
  - `core/`: Core functionality
    - `file_scanner.py`: Media file detection
    - `backup_system.py`: Backup and rollback functionality
    - `models.py`: Database models
  - `utils/`: Utility functions
    - `template_formatter.py`: Template formatting
    - `template_registry.py`: Template registration
    - `name_parser.py`: Filename parsing
    - `preview_system.py`: Preview generation
  - `config/`: Configuration management
  - `cli.py`: Command-line interface

## Documentation

Comprehensive documentation is available in the [docs](docs/) directory:

- [Getting Started Guide](docs/getting_started.md)
- [CLI Documentation](docs/cli/README.md)
- [Configuration System](docs/configuration/README.md)
- [File Utilities](docs/file-utils/README.md)
  - [Template System](docs/file-utils/template_system.md)
- [Episode Handling](docs/episode_handling.md)
- [Metadata System](docs/metadata/README.md)
- [Metadata-Episode Integration](docs/metadata/episode_integration.md)
- [Backend Architecture](docs/backend/README.md)
  - [MediaType System](docs/backend/media_type.md)
- [Database Schema](docs/database/README.md)
- [API Integration](docs/api/README.md)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgements

### TheTVDB
This product uses the TVDB API but is not endorsed or certified by TheTVDB.com or its affiliates.

![TheTVDB](https://thetvdb.com/images/attribution/logo2.png)

## License

This project is licensed under the GPL-2.0 License - see the [LICENSE](LICENSE) file for details.

## Testing

We've standardized our testing approach using pytest. The project aims to have comprehensive test coverage for all components.

### Current Test Status

- 509 passing tests
- 24 failing tests (being addressed)
- 51 skipped tests

### Running Tests

To run all tests:

```bash
python -m pytest
```

To run a specific test:

```bash
python -m pytest tests/path/to/test_file.py
```

For verbose output:

```bash
python -m pytest -v
```

For coverage report:

```bash
python -m pytest --cov=plexomatic
```
