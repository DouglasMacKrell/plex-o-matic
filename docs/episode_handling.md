# Episode Handling

Plex-o-matic includes robust support for handling various TV show episode formats, including multi-episode files, special episodes, and season packs.

## Multi-Episode Detection

The system can detect various multi-episode formats in filenames:

- Standard format: `Show.S01E01E02.mp4`
- Hyphen format: `Show.S01E01-E02.mp4`
- Dash format without E: `Show.S01E01-02.mp4`
- X format (common in anime): `Show 01x02-03.mp4`
- Space separator: `Show S01E01 E02.mp4`
- Text separators: `Show S01E05 to E07.mp4`, `Show S01E05 & E06.mp4`, `Show S01E05+E06.mp4`

## Special Episode Detection

Special episodes are detected and handled appropriately:

- Season 0 specials: `Show.S00E01.Special.mp4`
- Special keyword: `Show.Special.mp4`, `Show.Special1.mp4`
- OVA (Original Video Animation): `Show.OVA.mp4`, `Show.OVA1.mp4`, `Show.OVA.1.mp4`
- Movies/Films: `Show.Movie.mp4`, `Show.Film.mp4`, `Show.Movie.1.mp4`

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