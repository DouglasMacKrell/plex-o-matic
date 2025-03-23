# Template System

The template system in Plex-o-matic provides a flexible way to customize the naming patterns for your media files. This documentation explains how to use the template system, its components, and how to create and manage your own templates.

## Overview

The template system consists of several components:

1. **Template Registry**: Central registry for template management
2. **Template Manager**: Handles loading and saving templates to disk
3. **Template Formatter**: Processes templates and replaces variables with values
4. **Multi-Episode Formatter**: Specialized handling for multi-episode files
5. **Default Formatters**: Standard formatters for common media types

## Template Syntax

Templates use a simple variable substitution syntax with curly braces:

```
{variable_name}
```

You can also specify format options using Python's format syntax:

```
{variable_name:format_spec}
```

For example, to pad episode numbers with zeros to two digits:

```
{episode:02d}
```

## Available Variables

Depending on the media type, different variables are available:

### Common Variables
- `title`: The title of the show or movie
- `extension`: The file extension (including the dot)
- `quality`: The quality designation (e.g., "720p", "1080p")

### TV Show Variables
- `season`: The season number
- `episode`: The episode number
- `episode_title`: The title of the episode
- `year`: The year of release (if available)

### Movie Variables
- `year`: The year of release
- `resolution`: The resolution (e.g., "1080p")

### Anime Variables
- `group`: The release group
- `episode`: The episode number
- `quality`: The quality designation

## Default Templates

Plex-o-matic includes default templates for common media types:

### TV Show
```
{title}.S{season:02d}E{episode:02d}{extension}
```

Example: `Breaking.Bad.S01E05.mp4`

### Movie
```
{title}.{year}{extension}
```

Example: `Inception.2010.mp4`

### Anime
```
[{group}] {title} - {episode:02d} [{quality}]{extension}
```

Example: `[HorribleSubs] Attack on Titan - 01 [720p].mkv`

## Multi-Episode Formatting

The template system includes special handling for multi-episode files:
```
{title}.S{season:02d}E{episode:02d}{extension}
```

For a file with episodes 1-3, this would render as:
```
Show.Name.S01E01-E03.mp4
```

## Custom Templates

You can create and register your own templates. The system stores templates in the following locations:

- **Default templates**: `plexomatic/utils/templates/default/`
- **Custom templates**: `plexomatic/utils/templates/custom/`

## Template API

### Replacing Variables

The primary function for formatting strings is `replace_variables`:

```python
from plexomatic.utils.template_formatter import replace_variables
from plexomatic.utils.name_parser import ParsedMediaName, MediaType

parsed = ParsedMediaName(
    media_type=MediaType.TV_SHOW,
    title="Breaking Bad",
    season=1,
    episodes=[5],
    extension="mp4"
)

template = "{title}.S{season:02d}E{episode:02d}{extension}"
result = replace_variables(template, parsed)
# Result: "Breaking.Bad.S01E05.mp4"
```

### Applying Templates

You can use the higher-level `apply_template` function to apply a named template:

```python
from plexomatic.utils.template_formatter import apply_template
from plexomatic.utils.name_parser import ParsedMediaName, MediaType

parsed = ParsedMediaName(
    media_type=MediaType.TV_SHOW,
    title="Breaking Bad",
    season=1,
    episodes=[5],
    extension="mp4"
)

result = apply_template(parsed, "tv_show")
# Result: "Breaking.Bad.S01E05.mp4"
```

## Deprecated Functions

The `format_template` function is deprecated and will be removed in a future release. Use `replace_variables` instead.

## Implementation Details

The template system was refactored from a monolithic implementation into smaller, focused modules:

- `template_types.py`: Enums, constants, and helper functions
- `template_manager.py`: Template loading and management
- `template_formatter.py`: Core formatting functionality
- `multi_episode_formatter.py`: Multi-episode handling
- `default_formatters.py`: Media type-specific default formatters
- `template_registry.py`: Public API for template registration

This modular design makes the system more maintainable and extensible.
