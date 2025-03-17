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