# Plex-o-matic

An intelligent media file organization tool for Plex that helps automate the process of renaming and structuring media files for optimal Plex compatibility.

## Features

- Automated media file renaming and organization
- Multi-episode file handling
- TVDB/TMDB integration for metadata verification
- Local LLM integration for complex name parsing
- Safe rename operations with backup/restore capability
- Preview system for verifying changes
- Support for TV Shows, Movies, and Music

## Installation

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

## Configuration

1. Copy the example configuration:
```bash
cp config/config.example.yaml config/config.yaml
```

2. Edit `config/config.yaml` with your settings:
- API keys for TVDB/TMDB
- Media directories
- Local LLM settings
- Naming preferences

## Usage

Basic usage:
```bash
plexomatic scan /path/to/media  # Scan and analyze media files
plexomatic preview             # Preview proposed changes
plexomatic apply              # Apply changes
plexomatic rollback           # Rollback last operation
```

## Development

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

## License

This project is licensed under the GPL-2.0 License - see the [LICENSE](LICENSE) file for details. 