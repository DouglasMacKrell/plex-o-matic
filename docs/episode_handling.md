![Plex-O-Matic Title Image](../public/Plex-O-Matic_README_Title_Image.webp)

# Episode Handling

Plex-o-matic includes robust support for handling various TV show episode formats, including multi-episode files, special episodes, and season packs.

## Media Types

Plex-o-matic supports the following media types for proper handling:

- **TV_SHOW**: Regular TV show episodes
- **MOVIE**: Movie files
- **ANIME**: Anime TV series episodes
- **TV_SPECIAL**: Special episodes for TV shows (OVAs, extras, etc.)
- **ANIME_SPECIAL**: Special episodes for anime series (OVAs, specials, movies)

Each media type has specific naming conventions and handling logic that optimizes organization for Plex.

## Multi-Episode Detection

The system can detect various multi-episode formats in filenames:

- Standard format: `Show.S01E01E02.mp4`
- Hyphen format: `Show.S01E01-E02.mp4`
- Dash format without E: `Show.S01E01-02.mp4`
- X format (common in anime): `Show 01x02-03.mp4`
- Space separator: `Show S01E01 E02.mp4`
- Text separators: `Show S01E05 to E07.mp4`, `Show S01E05 & E06.mp4`, `Show S01E05+E06.mp4`

## Anthology Show Handling

Plex-o-matic provides special support for anthology shows where multiple episodes are combined into a single file but may be labeled with a single episode number. This is common in animated shows and certain TV series.

### Configuration

```python
# In config.json or via CLI
{
    "episode_handling": {
        "anthology_mode": true,
        "title_match_priority": 0.8,  # Weight given to title matches vs episode numbers
        "infer_from_directory": true,  # Enable directory structure inference
        "match_threshold": 0.7  # Minimum confidence score for title matches
    }
}
```

### Example Usage

```python
from plexomatic.utils.episode_handler import process_anthology_episode

# Example with multiple segments in title
result = process_anthology_episode(
    "Chip N Dale Park Life-S01E01-Thou Shall Nut Steal The Baby Whisperer It Takes Two To Tangle",
    anthology_mode=True
)
# Result: {
#   'episode_numbers': [1, 2, 3],
#   'segments': [
#       "Thou Shall Nut Steal",
#       "The Baby Whisperer",
#       "It Takes Two To Tangle"
#   ]
# }
```

### Title-Based Matching

When anthology mode is enabled, the system will:
1. Extract potential episode titles from the filename
2. Query the metadata provider for official episode listings
3. Use fuzzy matching to identify multiple episodes
4. Generate appropriate episode ranges
5. Apply confidence scoring to prevent false matches

```python
from plexomatic.utils.episode_handler import match_episode_titles

matches = match_episode_titles(
    ["Thou Shall Nut Steal", "The Baby Whisperer"],
    show_id="12345",
    season=1
)
# Returns matched episodes with confidence scores
```

### Directory Structure Inference

When files lack complete information, the system can infer series names from directory structure:

```python
from plexomatic.utils.episode_handler import infer_series_info

# Given a structure like:
# Batman The Animated Series/
#   S1/
#     01.mp4
#     02.mp4

info = infer_series_info("/path/to/01.mp4")
# Returns: {
#   'series_name': "Batman The Animated Series",
#   'season': 1
# }
```

## Special Episode Detection

Special episodes are detected and handled appropriately:

- Season 0 specials: `Show.S00E01.Special.mp4`
- Special keyword: `Show.Special.mp4`, `Show.Special1.mp4`
- OVA (Original Video Animation): `Show.OVA.mp4`, `Show.OVA1.mp4`, `Show.OVA.1.mp4`
- Movies/Films: `Show.Movie.mp4`, `Show.Film.mp4`, `Show.Movie.1.mp4`

### Media Type Classification

Special episodes are automatically classified with the appropriate media type:

- **TV_SPECIAL**: Used for TV show specials, extras, OVAs, and behind-the-scenes content
  - Example patterns: `Show.Special.mp4`, `Show.OVA.mp4`, `Show.Extra.mp4`
  - Typically placed in Season 0 (Specials) folder in Plex

- **ANIME_SPECIAL**: Used for anime specials, OVAs, and movies related to a series
  - Example patterns: `[Group] Show OVA [1080p].mkv`, `[Group] Show - Special 1 [720p].mkv`
  - Often includes group/fansub information and quality tags

### Template Handling

Each special type uses appropriate templates for file naming:

```python
from plexomatic.utils.name_templates import get_template_for_media_type
from plexomatic.core.models import MediaType

# Get template for TV specials
tv_special_template = get_template_for_media_type(MediaType.TV_SPECIAL)
# Uses the same template as TV shows but with special handling

# Get template for anime specials
anime_special_template = get_template_for_media_type(MediaType.ANIME_SPECIAL)
# Uses the same template as anime but with special handling
```

Special episodes are typically organized into Season 0 in Plex's naming structure, which is reflected in the file naming.

## Season Pack Organization

When processing a season pack, files are automatically organized into appropriate folders:

- Regular episodes go into season folders: `Season 1`, `Season 2`, etc.
- Special episodes go into a `Specials` folder
- Unrecognized files go into an `Unknown` folder

## Filename Formatting

When generating filenames for multi-episode files, the system supports:

- Sequential episodes as ranges: `Show.S01E01-E03.Title.mp4`
- Non-sequential episodes as concatenated: `Show.S01E01+E03+E05.Title.mp4`

## Usage in Code

### Detecting Multi-Episodes

```python
from plexomatic.utils.episode_handler import detect_multi_episodes

# Returns a list of episode numbers: [1, 2, 3]
episodes = detect_multi_episodes("Show.S01E01E02E03.mp4")

# Returns a list with a single episode: [1]
episodes = detect_multi_episodes("Show.S01E01.mp4")
```

### Formatting Multi-Episode Filenames

```python
from plexomatic.utils.name_utils import generate_tv_filename

# Standard single episode
filename = generate_tv_filename("Show Name", 1, 5, "Episode Title")
# Result: "Show.Name.S01E05.Episode.Title.mp4"

# Sequential multi-episode
filename = generate_tv_filename("Show Name", 1, [5, 6, 7], "Multi Episode")
# Result: "Show.Name.S01E05-E07.Multi.Episode.mp4"

# Non-sequential multi-episode
filename = generate_tv_filename("Show Name", 1, [1, 3, 5], "Multi Episode", concatenated=True)
# Result: "Show.Name.S01E01+E03+E05.Multi.Episode.mp4"
```

### Detecting Special Episodes

```python
from plexomatic.utils.episode_handler import detect_special_episodes

# Returns {'type': 'special', 'number': 1}
special_info = detect_special_episodes("Show.S00E01.Special.mp4")

# Returns {'type': 'ova', 'number': None}
special_info = detect_special_episodes("Show.OVA.mp4")

# Returns None for regular episodes
special_info = detect_special_episodes("Show.S01E01.mp4")
```

### Organizing Season Packs

```python
from pathlib import Path
from plexomatic.utils.episode_handler import organize_season_pack

files = [
    Path("/media/Show.S01E01.mp4"),
    Path("/media/Show.S01E02.mp4"),
    Path("/media/Show.S02E01.mp4"),
    Path("/media/Show.Special.mp4")
]

# Returns a dictionary with season folders as keys
result = organize_season_pack(files)
# Result: {
#   "Season 1": [Path("/media/Show.S01E01.mp4"), Path("/media/Show.S01E02.mp4")],
#   "Season 2": [Path("/media/Show.S02E01.mp4")],
#   "Specials": [Path("/media/Show.Special.mp4")],
#   "Unknown": []
# }
```

## Metadata Integration

The episode handling system is fully integrated with the metadata system, allowing for advanced features:

### Special Episode Metadata

When a special episode is detected, the system can fetch specific metadata for it from providers:

```python
from plexomatic.metadata.manager import MetadataManager
from plexomatic.utils.episode_handler import detect_special_episodes

# Detect special episode information
special_info = detect_special_episodes("Show.Special.1.mp4")
if special_info:
    # Create a metadata manager
    manager = MetadataManager()

    # First match the show
    match_result = manager.match("Show.mp4")
    if match_result.matched:
        # Fetch special episode metadata
        special_metadata = manager.fetch_episode_metadata(
            match_result.id,
            {
                "special_type": special_info["type"],
                "special_number": special_info["number"]
            }
        )

        # Use the metadata to generate a filename
        from plexomatic.utils.episode_handler import generate_filename_from_metadata
        new_filename = generate_filename_from_metadata("Show.Special.1.mp4", special_metadata)
        # Result: "Show.S00E01.Special.Episode.Title.mp4"
```

### Multi-Episode Metadata

Similarly, when multiple episodes are detected in a file, metadata for all episodes can be fetched:

```python
from plexomatic.metadata.manager import MetadataManager
from plexomatic.utils.episode_handler import detect_multi_episodes

# Detect multi-episode information
episodes = detect_multi_episodes("Show.S01E01E02E03.mp4")
if len(episodes) > 1:
    # Create a metadata manager
    manager = MetadataManager()

    # First match the show
    match_result = manager.match("Show.mp4")
    if match_result.matched:
        # Fetch multi-episode metadata
        multi_episode_metadata = manager.fetch_episode_metadata(
            match_result.id,
            {
                "episodes": episodes,
                "season": 1  # Season number from the filename
            }
        )

        # Use the metadata to generate a filename
        from plexomatic.utils.episode_handler import generate_filename_from_metadata
        new_filename = generate_filename_from_metadata("Show.S01E01E02E03.mp4", multi_episode_metadata)
        # Result: "Show.S01E01-E03.Episode.Titles.mp4"
```

### Generating Filenames from Metadata

The `generate_filename_from_metadata` function provides a unified way to create filenames based on metadata and episode information:

```python
from plexomatic.utils.episode_handler import generate_filename_from_metadata

# Regular episode
regular_metadata = {
    "title": "Show Name",
    "season": 1,
    "episode": 5,
    "episode_title": "Episode Title"
}
regular_filename = generate_filename_from_metadata("original.mp4", regular_metadata)
# Result: "Show.Name.S01E05.Episode.Title.mp4"

# Special episode
special_metadata = {
    "title": "Show Name",
    "special_type": "special",
    "special_number": 1,
    "special_episode": {
        "title": "Behind the Scenes"
    }
}
special_filename = generate_filename_from_metadata("original.mp4", special_metadata)
# Result: "Show.Name.S00E01.Behind.the.Scenes.mp4"

# Multi-episode
multi_metadata = {
    "title": "Show Name",
    "season": 1,
    "episode_numbers": [1, 2, 3],
    "multi_episodes": [
        {"title": "Part 1"},
        {"title": "Part 2"},
        {"title": "Part 3"}
    ]
}
multi_filename = generate_filename_from_metadata("original.mp4", multi_metadata)
# Result: "Show.Name.S01E01-E03.Part.1.&.Part.2.&.Part.3.mp4"
```

This integration allows for more accurate and comprehensive metadata-based episode handling, ensuring that files are named correctly even in complex scenarios like special episodes and multi-episode files.
