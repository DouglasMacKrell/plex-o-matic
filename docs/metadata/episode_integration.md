# Metadata-Episode Integration

Plex-o-matic features a powerful integration between the metadata system and episode handling, enabling accurate detection, matching, and filename generation for complex episode scenarios.

## Overview

The integration consists of several key components:

1. **Enhanced Detection** - Special episode and multi-episode detection in the metadata match process
2. **Episode-Specific Metadata Fetching** - Retrieving detailed metadata for specific episodes
3. **Intelligent Filename Generation** - Creating standardized filenames based on episode metadata

## Detection in Metadata Match

The `MetadataManager.match()` method has been enhanced to detect special episodes and multi-episodes:

```python
from plexomatic.metadata.manager import MetadataManager
from plexomatic.metadata.fetcher import MediaType

manager = MetadataManager()

# Match a filename that contains a special episode
result = manager.match("Show.Name.Special.mp4", MediaType.TV_SHOW)
if result.matched and "special_type" in result.metadata:
    print(f"Detected special: {result.metadata['special_type']}")

# Match a filename that contains multiple episodes
result = manager.match("Show.Name.S01E01E02E03.mp4", MediaType.TV_SHOW)
if result.matched and "episodes" in result.metadata:
    print(f"Detected episodes: {result.metadata['episodes']}")
```

The detection happens early in the match process, allowing for specialized handling before standard metadata search.

## Episode-Specific Metadata Fetching

The `fetch_episode_metadata()` method allows retrieving detailed metadata for special episodes and multi-episodes:

```python
from plexomatic.metadata.manager import MetadataManager

manager = MetadataManager()

# Fetch metadata for a special episode
special_metadata = manager.fetch_episode_metadata(
    "tvdb:12345",  # Show ID
    {
        "special_type": "special",
        "special_number": 1
    }
)

# Fetch metadata for a multi-episode file
multi_metadata = manager.fetch_episode_metadata(
    "tvdb:12345",  # Show ID
    {
        "episodes": [1, 2, 3],
        "season": 1
    }
)
```

### Special Episode Metadata

For special episodes, the method returns the base show metadata enriched with special episode information:

```python
# Example special episode metadata
{
    "id": "tvdb:12345",
    "title": "Show Name",
    "overview": "Show description",
    "year": 2020,
    "special_type": "special",  # Type (special, ova, movie)
    "special_number": 1,        # Episode number within the special type
    "special_episode": {        # Detailed episode information
        "id": 67890,
        "title": "Behind the Scenes",
        "overview": "A special behind-the-scenes episode",
        "special_number": 1,
        "air_date": "2020-05-01"
    }
}
```

### Multi-Episode Metadata

For multi-episode files, the method returns the base show metadata enriched with information about all included episodes:

```python
# Example multi-episode metadata
{
    "id": "tvdb:12345",
    "title": "Show Name",
    "overview": "Show description",
    "year": 2020,
    "episode_numbers": [1, 2, 3],  # List of episode numbers
    "multi_episodes": [            # Detailed information for each episode
        {
            "id": 67890,
            "title": "Episode 1",
            "overview": "First episode",
            "season": 1,
            "episode": 1,
            "air_date": "2020-01-01"
        },
        {
            "id": 67891,
            "title": "Episode 2",
            "overview": "Second episode",
            "season": 1,
            "episode": 2,
            "air_date": "2020-01-08"
        },
        {
            "id": 67892,
            "title": "Episode 3",
            "overview": "Third episode",
            "season": 1,
            "episode": 3,
            "air_date": "2020-01-15"
        }
    ]
}
```

## Intelligent Filename Generation

The `generate_filename_from_metadata()` function in the episode handler uses metadata to create standardized filenames:

```python
from plexomatic.utils.episode_handler import generate_filename_from_metadata

# Generate filename for a regular episode
regular_filename = generate_filename_from_metadata(
    "original.mp4",
    {
        "title": "Show Name",
        "season": 1,
        "episode": 5,
        "episode_title": "Episode Title"
    }
)
# Result: "Show.Name.S01E05.Episode.Title.mp4"

# Generate filename for a special episode
special_filename = generate_filename_from_metadata(
    "original.mp4",
    {
        "title": "Show Name",
        "special_type": "ova",
        "special_number": 2,
        "special_episode": {
            "title": "OVA Episode"
        }
    }
)
# Result: "Show.Name.S00E02.OVA.Episode.mp4"

# Generate filename for multi-episodes
multi_filename = generate_filename_from_metadata(
    "original.mp4",
    {
        "title": "Show Name",
        "season": 1,
        "episode_numbers": [1, 2, 3],
        "multi_episodes": [
            {"title": "Part 1"},
            {"title": "Part 2"},
            {"title": "Part 3"}
        ]
    }
)
# Result: "Show.Name.S01E01-E03.Part.1.&.Part.2.&.Part.3.mp4"
```

The function handles different episode types:
- Regular episodes use standard TV show naming (S01E01)
- Special episodes use S00 season and appropriate numbering
- Multi-episodes use range format (E01-E03) for sequential episodes or concatenated format (E01+E03+E05) for non-sequential episodes
- Episode titles are combined for multi-episodes

## Complete Integration Example

Here's a complete example showing the entire workflow:

```python
from plexomatic.metadata.manager import MetadataManager
from plexomatic.utils.episode_handler import detect_multi_episodes, generate_filename_from_metadata

# 1. Create the metadata manager
manager = MetadataManager()

# 2. Detect episode type from filename
filename = "Show.S01E01E02E03.mp4"
episodes = detect_multi_episodes(filename)

if len(episodes) > 1:
    # 3. Match the show to get its ID
    match_result = manager.match("Show.mp4", media_type=MediaType.TV_SHOW)

    if match_result.matched:
        # 4. Fetch detailed metadata for the episodes
        episode_metadata = manager.fetch_episode_metadata(
            match_result.id,
            {
                "episodes": episodes,
                "season": 1  # Season from the filename
            }
        )

        # 5. Generate a standardized filename
        new_filename = generate_filename_from_metadata(filename, episode_metadata)

        print(f"Original: {filename}")
        print(f"New: {new_filename}")
```

This integration ensures that all episode types are properly handled with accurate metadata, creating consistent and informative filenames.

## Advanced Usage

### Custom Episode Title Formatting

You can customize how episode titles are handled in multi-episode files:

```python
# Get the episode metadata
multi_metadata = manager.fetch_episode_metadata("tvdb:12345", {"episodes": [1, 2, 3], "season": 1})

# Customize the episode titles
titles = [ep.get("title") for ep in multi_metadata["multi_episodes"] if ep.get("title")]
custom_title = " + ".join(titles)

# Update the metadata
multi_metadata["custom_title"] = custom_title

# Generate the filename
custom_filename = generate_filename_from_metadata("original.mp4", multi_metadata)
```

### Integration with File Operations

The integration works seamlessly with file operations:

```python
from plexomatic.utils.file_ops import rename_file

# Get the metadata and generate the new filename
new_filename = generate_filename_from_metadata(original_path.name, metadata)

# Create the new path
new_path = original_path.parent / new_filename

# Perform the rename with backup
rename_file(str(original_path), str(new_path), create_backup=True)
```

This integration is a core component of Plex-o-matic, enhancing the system's ability to handle complex episode scenarios with accurate metadata.
