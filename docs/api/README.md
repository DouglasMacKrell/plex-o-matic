# API Integration

Plex-o-matic integrates with external APIs to fetch metadata for media files and leverage local AI for enhanced file analysis.

## Available API Clients

### TVDB Client

The TVDB client provides access to TV show metadata from thetvdb.com API.

> **Note**: This product uses the TVDB API but is not endorsed or certified by TheTVDB.com or its affiliates. When using TVDB data in your application, you must include proper attribution as per their licensing requirements.

```python
from plexomatic.api.tvdb_client import TVDBClient

# Initialize the client with your API key
client = TVDBClient(api_key="your_tvdb_api_key")

# Authenticate with the API
client.authenticate()

# Search for a TV series by name
results = client.get_series_by_name("Breaking Bad")

# Get detailed information about a specific series
series = client.get_series_by_id(series_id=12345)

# Get episodes for a series
episodes = client.get_episodes_by_series_id(series_id=12345)
```

Features:
- Authentication and token management
- Automatic token renewal when expired
- Request caching for better performance
- Rate limiting protection and automatic retries
- Comprehensive error handling

### TMDB Client

The TMDB client provides access to movie and TV show metadata from themoviedb.org API.

```python
from plexomatic.api.tmdb_client import TMDBClient

# Initialize the client with your API key
client = TMDBClient(api_key="your_tmdb_api_key")

# Get API configuration (image URLs and sizes)
config = client.get_configuration()

# Search for movies
movie_results = client.search_movie("The Matrix", year=1999)

# Search for TV shows
tv_results = client.search_tv("Stranger Things")

# Get movie details
movie = client.get_movie_details(movie_id=603)  # The Matrix

# Get TV show details
show = client.get_tv_details(tv_id=66732)  # Stranger Things

# Get TV season details
season = client.get_tv_season(tv_id=66732, season_number=1)

# Get a full poster URL
poster_url = client.get_poster_url(poster_path="/poster.jpg", size="w500")
```

Features:
- Configuration retrieval for image URLs
- Movie and TV show searching
- Detailed metadata for movies, TV shows, and seasons
- Request caching for better performance
- Image URL helper functions
- Rate limiting protection

### AniDB Client

The AniDB client provides access to anime metadata from the AniDB database through both its UDP and HTTP APIs.

```python
from plexomatic.api.anidb_client import AniDBClient

# Initialize the client with your AniDB credentials
client = AniDBClient(
    username="your_anidb_username",
    password="your_anidb_password",
    client_name="plexomatic",  # Registered client name
    client_version=1
)

# Search for anime by name
anime = client.get_anime_by_name("Cowboy Bebop")

# Get anime by ID
anime_details = client.get_anime_details(anime_id=1)  # Cowboy Bebop

# Get episodes for anime
episodes = client.get_episodes_with_titles(anime_id=1)

# Map a title to the most likely anime series
matched_anime = client.map_title_to_series("Cowboy Bebop")
```

Features:
- Combined access to both UDP and HTTP AniDB APIs
- Authentication and session management
- Anime searching by name or ID
- Comprehensive episode information retrieval
- Title matching with fuzzy search
- Automatic rate limiting protection
- Error handling for common AniDB API issues

### TVMaze Client

The TVMaze client provides access to TV show metadata from the TVMaze API, including show information, episodes, and cast data.

```python
from plexomatic.api.tvmaze_client import TVMazeClient

# Initialize the client
client = TVMazeClient(cache_size=100)

# Search for TV shows by name
shows = client.search_shows("Breaking Bad")

# Get detailed information about a specific show by ID
show = client.get_show_by_id(show_id=1)

# Get show information using an IMDB ID
show = client.get_show_by_imdb_id("tt0903747")  # Breaking Bad

# Get all episodes for a show
episodes = client.get_episodes(show_id=1)

# Get a specific episode by season and episode number
episode = client.get_episode_by_number(show_id=1, season=1, episode=1)

# Search for people by name
people = client.search_people("Bryan Cranston")

# Get the cast for a show
cast = client.get_show_cast(show_id=1)

# Clear the cache if needed
client.clear_cache()
```

Features:
- Show search by name and retrieval by ID
- IMDB ID lookup support
- Comprehensive episode information
- Cast information for shows
- People search functionality
- Efficient request caching
- Rate limiting protection
- Robust error handling

### Local LLM Client

The Local LLM client provides integration with Ollama for local AI inferencing, specifically with the Deepseek R1 8b model.

```python
from plexomatic.api.llm_client import LLMClient

# Initialize the client
client = LLMClient(
    model_name="deepseek-r1:8b",
    base_url="http://localhost:11434"
)

# Check if the model is available
if client.check_model_available():
    # Generate text with the LLM
    response = client.generate_text(
        prompt="What is the plot of Breaking Bad?",
        temperature=0.7,
        max_tokens=512
    )

    # Analyze a filename to extract metadata
    metadata = client.analyze_filename("BreakingBad.S01E01.720p.HDTV.x264.mp4")
    # Returns: {"title": "Breaking Bad", "season": 1, "episode": 1, ...}

    # Get a standardized filename suggestion
    new_filename = client.suggest_filename(
        original_filename="BreakingBad.S01E01.720p.HDTV.x264.mp4",
        title="Breaking Bad",
        episode_title="Pilot"
    )
    # Returns: "Breaking Bad - S01E01 - Pilot [720p-HDTV-x264].mp4"
```

Features:
- Local model availability checking
- Text generation with customizable parameters
- Media filename analysis for metadata extraction
- Standardized filename suggestions
- Error handling with JSON parsing recovery

## Usage in the Application

These API clients are used in Plex-o-matic to:

1. Fetch accurate metadata for TV shows and movies
2. Extract information from filenames when standard patterns don't match
3. Generate standardized filenames based on metadata
4. Enhance the quality of file organization

## Configuration

API keys and settings are managed through the application's configuration system:

```json
{
    "api": {
        "tvdb": {
            "api_key": "your_tvdb_api_key",
            "cache_size": 100,
            "auto_retry": true
        },
        "tmdb": {
            "api_key": "your_tmdb_api_key",
            "cache_size": 100
        },
        "anidb": {
            "username": "your_anidb_username",
            "password": "your_anidb_password",
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
