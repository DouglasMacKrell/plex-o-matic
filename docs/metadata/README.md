![Plex-O-Matic Title Image](../../public/Plex-O-Matic_README_Title_Image.webp)

# Metadata Management System

The Metadata Management system in Plex-o-matic provides a unified interface for searching, matching, and managing metadata from multiple sources. It allows the application to intelligently combine results from different providers (TVDB, TMDB, AniDB, TVMaze) and select the best match for a given media file.

## Components

### MetadataManager

The `MetadataManager` class is the central component that coordinates metadata operations across different sources.

```python
from plexomatic.metadata.manager import MetadataManager
from plexomatic.metadata.fetcher import TVDBMetadataFetcher, TMDBMetadataFetcher

# Create fetchers for each source
tvdb_fetcher = TVDBMetadataFetcher()
tmdb_fetcher = TMDBMetadataFetcher()

# Initialize the metadata manager with the fetchers
manager = MetadataManager(
    tvdb_fetcher=tvdb_fetcher,
    tmdb_fetcher=tmdb_fetcher
)

# Search across all sources
results = manager.search("Breaking Bad", media_type=MediaType.TV_SHOW)

# Match a filename to the best metadata
match_result = manager.match("Breaking.Bad.S01E01.720p.mkv", media_type=MediaType.TV_SHOW)
if match_result.matched:
    print(f"Found match: {match_result.title} ({match_result.year})")
    print(f"Confidence: {match_result.confidence}")

# Fetch detailed metadata for a specific ID
metadata = manager.fetch_metadata("tvdb-123456")

# Clear the cache if needed
manager.clear_cache()
```

### MetadataMatchResult

The `MetadataMatchResult` class represents the result of a metadata match operation.

```python
# Example match result
match_result = MetadataMatchResult(
    matched=True,
    title="Breaking Bad",
    year=2008,
    media_type=MediaType.TV_SHOW,
    confidence=0.95,
    metadata={"id": "tvdb:12345", "title": "Breaking Bad", "year": 2008, ...}
)

# Accessing match result properties
if match_result.matched:
    print(f"ID: {match_result.id}")
    print(f"Source: {match_result.source}")
    print(f"Title: {match_result.title}")
    print(f"Year: {match_result.year}")
    print(f"Confidence: {match_result.confidence}")
```

## Features

### Multi-Source Search

The metadata manager can search across multiple sources simultaneously and aggregate the results based on relevance and confidence.

```python
# Search across all relevant sources for TV shows
tv_results = manager.search("Breaking Bad", media_type=MediaType.TV_SHOW)

# Search across all relevant sources for movies
movie_results = manager.search("The Matrix", media_type=MediaType.MOVIE)

# Search across all relevant sources for anime
anime_results = manager.search("Naruto", media_type=MediaType.ANIME)

# Search across all sources (TV, movies, anime)
all_results = manager.search("Avatar", media_type=None)
```

### Intelligent Filename Matching

The metadata manager can extract information from filenames and match them to the best metadata result.

```python
# Match a TV show filename
tv_match = manager.match("Breaking.Bad.S01E01.720p.mkv", media_type=MediaType.TV_SHOW)

# Match a movie filename
movie_match = manager.match("The.Matrix.1999.1080p.BluRay.x264.mkv", media_type=MediaType.MOVIE)

# Match an anime filename
anime_match = manager.match("[Group] Naruto - 001 [720p].mkv", media_type=MediaType.ANIME)

# Match without specifying media type (will try all types)
auto_match = manager.match("Breaking.Bad.S01E01.720p.mkv")
```

### Flexible ID Format

The metadata manager supports a unified ID format that includes the source prefix:

- TVDB: `tvdb-12345`
- TMDB: `tmdb-12345`
- AniDB: `anidb-12345`
- TVMaze: `tvmaze-12345`

```python
# Fetch metadata using IDs from different sources
tvdb_metadata = manager.fetch_metadata("tvdb-12345")
tmdb_metadata = manager.fetch_metadata("tmdb-12345")
anidb_metadata = manager.fetch_metadata("anidb-12345")
tvmaze_metadata = manager.fetch_metadata("tvmaze-12345")
```

### Episode-Specific Metadata

The metadata manager can fetch specific metadata for special episodes and multi-episode files:

```python
# Fetch metadata for a special episode
special_episode_metadata = manager.fetch_episode_metadata(
    "tvdb-12345",
    {
        "special_type": "special",
        "special_number": 1
    }
)

# Fetch metadata for multiple episodes in a file
multi_episode_metadata = manager.fetch_episode_metadata(
    "tvdb-12345",
    {
        "episodes": [1, 2, 3],
        "season": 1
    }
)
```

#### Special Episode Metadata

For special episodes, the system fetches metadata specific to that episode type (specials, OVAs, movies):

```python
# The returned metadata includes special episode information
special_metadata = {
    "id": "tvdb-12345",
    "title": "Show Name",
    "special_type": "special",
    "special_episode": {
        "id": 67890,
        "title": "Behind the Scenes",
        "overview": "A behind-the-scenes look at the making of the show",
        "special_number": 1,
        "air_date": "2020-05-01"
    }
}
```

#### Multi-Episode Metadata

For multi-episode files, the system fetches metadata for all included episodes:

```python
# The returned metadata includes information for all episodes
multi_metadata = {
    "id": "tvdb-12345",
    "title": "Show Name",
    "episode_numbers": [1, 2, 3],
    "multi_episodes": [
        {
            "id": 67890,
            "title": "Part 1",
            "overview": "First part of the story",
            "season": 1,
            "episode": 1,
            "air_date": "2020-01-01"
        },
        {
            "id": 67891,
            "title": "Part 2",
            "overview": "Second part of the story",
            "season": 1,
            "episode": 2,
            "air_date": "2020-01-08"
        },
        {
            "id": 67892,
            "title": "Part 3",
            "overview": "Final part of the story",
            "season": 1,
            "episode": 3,
            "air_date": "2020-01-15"
        }
    ]
}
```

### Intelligent Episode Detection in Match

The metadata manager can automatically detect special episodes and multi-episodes during the match process:

```python
# Match a special episode
special_match = manager.match("Show.Special.1.mp4", media_type=MediaType.TV_SHOW)
if special_match.matched and "special_type" in special_match.metadata:
    print(f"Detected special: {special_match.metadata['special_type']}")
    print(f"Special number: {special_match.metadata['special_number']}")

# Match a multi-episode file
multi_match = manager.match("Show.S01E01E02E03.mp4", media_type=MediaType.TV_SHOW)
if multi_match.matched and "episodes" in multi_match.metadata:
    print(f"Detected episodes: {multi_match.metadata['episodes']}")
```

### Efficient Caching

The metadata manager includes an efficient caching mechanism to reduce API calls and improve performance.

```python
# Search results are cached
results1 = manager.search("Breaking Bad", media_type=MediaType.TV_SHOW)
# This will use the cache instead of making API calls
results2 = manager.search("Breaking Bad", media_type=MediaType.TV_SHOW)

# Clear the cache when needed
manager.clear_cache()
```

## Integration with File Operations

The metadata management system integrates with the file operations to provide metadata-enhanced filename standardization.

```python
# Scan a directory and match files to metadata
for file_path in file_scanner.scan_directory("/path/to/media"):
    # Determine the media type based on the path or filename
    media_type = determine_media_type(file_path)

    # Match the file to metadata
    match_result = manager.match(os.path.basename(file_path), media_type)

    if match_result.matched:
        # Generate a standardized filename using the metadata
        new_filename = generate_standardized_filename(
            title=match_result.title,
            year=match_result.year,
            media_type=match_result.media_type,
            # Additional metadata from match_result.metadata
        )

        # Create the new path
        new_path = os.path.join(os.path.dirname(file_path), new_filename)

        # Perform the rename operation
        file_ops.rename_file(file_path, new_path)
```

## Configuration

The metadata management system is configured through the application's configuration file:

```json
{
    "metadata": {
        "match_threshold": 0.6,
        "cache_size": 100,
        "preferred_sources": {
            "tv_show": ["tvdb", "tvmaze"],
            "movie": ["tmdb"],
            "anime": ["anidb"]
        }
    }
}
```

## Setting Up API Keys

To use the metadata sources, you need to set up API keys for TVDB, TMDB, and other services. Plex-o-matic provides an interactive CLI command to help with this:

```bash
plexomatic configure
```

This command will walk you through:
1. Entering your TVDB API key
2. Entering your TMDB API key
3. Configuring AniDB username and password (optional)
4. Setting up local LLM integration (optional)

The API keys will be saved in your configuration file at `~/.plexomatic/config.json` and used by the metadata management system when making API requests.
