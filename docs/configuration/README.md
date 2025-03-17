# Configuration System

Plex-o-matic provides a flexible configuration system that allows you to customize its behavior to suit your needs.

## Default Configuration

The default configuration includes:

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
            "cache_size": 100,
            "auto_retry": true
        },
        "tmdb": {
            "api_key": "",
            "cache_size": 100
        },
        "anidb": {
            "username": "",
            "password": "",
            "client_name": "plexomatic",
            "client_version": 1,
            "rate_limit_wait": 2.5
        },
        "tvmaze": {
            "cache_size": 100
        },
        "llm": {
            "model_name": "deepseek-r1:8b",
            "base_url": "http://localhost:11434",
            "temperature": 0.7
        }
    }
}
```

## Configuration File

Configuration is stored in JSON format at `~/.plexomatic/config.json` by default. The first time you run Plex-o-matic, this file will be created automatically with default values.

## Environment Variables

You can override the default configuration file location by setting the `PLEXOMATIC_CONFIG_PATH` environment variable:

```bash
export PLEXOMATIC_CONFIG_PATH="/path/to/your/config.json"
```

## Configuration Options

| Option | Type | Description |
|--------|------|-------------|
| `db_path` | String | Path to the SQLite database file. Supports `~` for home directory. |
| `log_level` | String | Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL) |
| `allowed_extensions` | List | File extensions to consider as media files |
| `ignore_patterns` | List | Filename patterns to ignore when scanning |
| `recursive_scan` | Boolean | Whether to scan directories recursively by default |
| `backup_enabled` | Boolean | Whether to enable the backup system |
| `api.tvdb.api_key` | String | Your API key for TVDB |
| `api.tvdb.cache_size` | Integer | Number of cached items for TVDB client |
| `api.tmdb.api_key` | String | Your API key for TMDB |
| `api.tmdb.cache_size` | Integer | Number of cached items for TMDB client |
| `api.anidb.username` | String | Your AniDB username |
| `api.anidb.password` | String | Your AniDB password |
| `api.anidb.client_name` | String | Registered client name for AniDB |
| `api.anidb.client_version` | Integer | Client version for AniDB |
| `api.anidb.rate_limit_wait` | Float | Time to wait between requests in seconds |
| `api.tvmaze.cache_size` | Integer | Number of cached items for TVMaze client |
| `api.llm.model_name` | String | Name of the Ollama model to use |
| `api.llm.base_url` | String | Base URL for the Ollama API |
| `api.llm.temperature` | Float | Temperature parameter for text generation |

## Modifying Configuration

You can edit the configuration file directly with a text editor, or use the API to modify it programmatically:

```python
from plexomatic.config import ConfigManager

# Initialize config
config = ConfigManager()

# Set a value
config.set("allowed_extensions", [".mp4", ".mkv"])

# Get a value
log_level = config.get("log_level")
```

## CLI Configuration Tool

Plex-o-matic provides an interactive CLI command to set up your configuration easily:

```bash
plexomatic configure
```

This interactive tool will guide you through setting up your API keys and other configuration settings. It will:

1. Prompt you for TVDB and TMDB API keys
2. Ask if you want to configure optional services like AniDB
3. Set up local LLM settings if desired
4. Save the configuration to the default location (`~/.plexomatic/config.json`)

This is the recommended way to set up your initial configuration and update API keys rather than editing the JSON file directly.

## Helper Methods

The `ConfigManager` class provides helper methods for common configuration values:

- `get_db_path()`: Returns the database path as a `Path` object
- `get_allowed_extensions()`: Returns the list of allowed file extensions
- `get_ignore_patterns()`: Returns the list of patterns to ignore

## Using in CLI

The CLI automatically uses the configuration system, so any changes you make to the configuration file will be reflected in CLI behavior. You can override many configuration options via command-line parameters:

```bash
# Override allowed extensions for this command
plexomatic scan --path /media/tv_shows --extensions ".mp4,.mkv"

# Override recursive scanning for this command
plexomatic scan --path /media/tv_shows --no-recursive
``` 