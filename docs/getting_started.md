# Getting Started with Plex-o-matic

This guide will walk you through installing Plex-o-matic, configuring it, and organizing your first media files. By the end, you'll have a working setup that helps automate the process of organizing your media library for Plex.

## Installation

### Prerequisites

Before installing Plex-o-matic, ensure you have:

- Python 3.8 or newer installed
- pip (Python package installer)
- git (if installing from source)

### Option 1: Install from PyPI (Recommended)

The simplest way to install Plex-o-matic is from PyPI:

```bash
pip install plex-o-matic
```

### Option 2: Install from Source

For the latest features or if you want to contribute to development:

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

3. Install the package in development mode:
```bash
pip install -e .
```

## Initial Configuration

The first time you run Plex-o-matic, you'll need to configure it with your API keys and preferences.

### Step 1: Run the Configuration Wizard

```bash
plexomatic configure
```

This interactive wizard will guide you through setting up:

- TVDB API key (for TV show metadata)
- TMDB API key (for movie metadata)
- Local LLM settings (optional, for AI-powered filename analysis)
- Default directories and preferences

### Step 2: Obtain API Keys

If you don't have API keys yet, here's how to get them:

#### TVDB API Key
1. Visit [TheTVDB.com](https://thetvdb.com/)
2. Register for an account
3. Go to your account page and request an API key
4. Enter this key in the configuration wizard

#### TMDB API Key
1. Visit [The Movie Database](https://www.themoviedb.org/)
2. Register for an account
3. Go to your account settings → API and request an API key
4. Enter this key in the configuration wizard

### Step 3: Configure Local LLM (Optional)

For AI-powered filename analysis, Plex-o-matic can use local language models via Ollama:

1. Install [Ollama](https://ollama.ai/download) on your machine
2. Pull the deepseek model:
```bash
ollama pull deepseek-r1:8b
```
3. Start Ollama before using Plex-o-matic features requiring LLM

## Basic Workflow

Plex-o-matic follows a simple but powerful workflow:

1. **Scan** your media files
2. **Preview** proposed changes
3. **Apply** changes to your files

### Step 1: Scan Media Files

Start by scanning a directory containing your media files:

```bash
plexomatic scan --path /path/to/your/media
```

This command will:
- Recursively scan all files in the directory
- Identify TV shows, movies, and anime
- Analyze filenames and extract metadata
- Store scan results for the next steps

Options:
- `--no-recursive`: Only scan the top-level directory
- `--extensions .mp4,.mkv`: Only scan specific file types
- `--verbose`: Show detailed output during scanning

### Step 2: Preview Changes

Before making any changes to your files, preview what Plex-o-matic would do:

```bash
plexomatic preview
```

This will show you:
- Current file names
- Proposed new file names
- Media type identified for each file
- Confidence level for the identification

Options:
- `--verbose`: Show more details about each file
- `--path /path/to/specific/folder`: Preview only files in a specific folder

### Step 3: Apply Changes

If you're satisfied with the previewed changes, apply them:

```bash
plexomatic apply
```

This will:
- Create a backup of the original files in the database
- Rename files according to Plex's naming conventions
- Organize files into appropriate directory structures
- Track all changes for potential rollback

Options:
- `--dry-run`: Show what would happen without making changes
- `--no-confirm`: Skip confirmation prompt (use with caution)

### Step 4: Rollback (If Needed)

If something goes wrong, you can easily roll back the changes:

```bash
plexomatic rollback
```

This will revert all files to their original state.

Options:
- `--operation-id 42`: Roll back a specific operation
- `--verbose`: Show detailed information during rollback

## Working with Templates

Plex-o-matic uses templates to format filenames. You can view and preview these templates:

### List Available Templates

```bash
plexomatic templates list
```

This shows all available template types and their formats.

### Show Specific Template

```bash
plexomatic templates show --type TV_SHOW
```

This shows the specific template used for TV shows.

### Preview Template with Sample Data

```bash
plexomatic templates show --type MOVIE --preview
```

This shows how the template would format a sample movie file.

## Common Examples

### Organizing a Complete TV Series

```bash
# Scan the TV series directory
plexomatic scan --path /downloads/MyTVShow

# Preview changes
plexomatic preview

# Apply changes
plexomatic apply
```

### Processing Multiple Media Types

```bash
# Scan a directory with mixed content
plexomatic scan --path /downloads/Mixed

# Preview changes, showing only movies
plexomatic preview --media-type MOVIE

# Apply changes for all media
plexomatic apply
```

### Working with Subtitle Files

Plex-o-matic automatically handles subtitle files found alongside your media:

```bash
# Scan a directory with media and subtitle files
plexomatic scan --path /media/with-subtitles

# See detailed subtitle information in the scan
plexomatic scan --path /media/with-subtitles --show-subtitles --verbose

# Preview changes including subtitle renaming
plexomatic preview

# Apply changes to both media and subtitle files
plexomatic apply
```

Subtitle files will be automatically matched to their media files and renamed according to Plex conventions.

### Using Different File Extensions

```bash
# Scan only specific file types
plexomatic scan --path /media --extensions .mp4,.mkv,.avi

# Define custom subtitle extensions
plexomatic scan --path /media --subtitle-extensions .srt,.vtt,.sub

# Preview and apply as usual
plexomatic preview
plexomatic apply
```

## Troubleshooting

### Common Issues

#### Files Not Being Detected

If files aren't being detected during scanning:

- Check if the file extensions are in your allowed extensions list
- Try running with `--verbose` to see more details
- Ensure you have read permissions on the files

#### Incorrect Media Type Detection

If files are being detected as the wrong media type:

- Try manually specifying the media type with `--media-type`
- Check if the filename follows standard conventions
- Ensure your API keys are correctly configured

#### API Rate Limiting

If you hit rate limits with the APIs:

- Reduce the number of files processed at once
- Wait a few minutes before trying again
- Check if your API key is valid

### Getting Help

If you encounter issues not covered here:

- Check the full [documentation](README.md)
- Open an issue on [GitHub](https://github.com/DouglasMacKrell/plex-o-matic/issues)
- Run commands with the `--verbose` flag to get more information

## Next Steps

Now that you have Plex-o-matic set up and working, you might want to:

- Explore advanced configuration options in the [Configuration Guide](configuration/README.md)
- Learn about the template system for customizing filenames in the [Template System Guide](file-utils/template_system.md)
- Understand how episode handling works in the [Episode Handling Guide](episode_handling.md)
- Set up automation for regularly processing new media files

## Additional Resources

- [CLI Documentation](cli/README.md) - Full command reference
- [Templates Documentation](file-utils/template_system.md) - Custom templates
- [API Integration](api/README.md) - Working with metadata sources
- [PLAN.md](../PLAN.md) - Project roadmap and upcoming features
