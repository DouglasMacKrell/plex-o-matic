![Plex-O-Matic Title Image](../public/Plex-O-Matic_README_Title_Image.webp)

# Plex-o-matic Documentation

## Introduction

Welcome to the Plex-o-matic documentation! This documentation provides comprehensive information about the architecture, components, and usage of Plex-o-matic, a powerful media file organization tool for Plex.

## Table of Contents

### Backend Documentation
- [Architecture Overview](backend/architecture.md)
  - Core Components
  - Operation Flow
  - Error Handling
  - Future Extensions

### Database Documentation
- [Schema Documentation](database/schema.md)
  - Table Definitions
  - Data Integrity
  - Backup and Maintenance
  - Usage Examples

### API Integration
- [API Clients](api/README.md)
  - TVDB API Client
  - TMDB API Client
  - AniDB API Client
  - TVMaze API Client
  - Local LLM Client (Ollama with Deepseek R1)
  - Usage Examples and Configuration

### Metadata Management
- [Metadata System](metadata/README.md)
  - MetadataManager
  - Multi-Source Aggregation
  - Intelligent Filename Matching
  - Confidence-Based Result Ranking
  - Caching Mechanisms

## Feature Documentation

- [CLI](cli/README.md) - Command-line interface documentation
- [Configuration](configuration/README.md) - Configuration system documentation
- [File Utilities](file-utils/README.md) - File operation utilities
- [Episode Handling](episode_handling.md) - TV show episode handling features
- [Metadata Management](metadata/README.md) - Metadata system architecture
- [Metadata-Episode Integration](metadata/episode_integration.md) - Integration between metadata system and episode handling
- [API Integration](api/README.md) - API integration with external services
- [Database](database/README.md) - Database schema and operation tracking
- [Backend](backend/README.md) - Backend system architecture

## Quick Start

1. Install the package:
   ```bash
   pip install plex-o-matic
   ```

2. Configure your API keys and settings:
   ```bash
   plexomatic configure
   ```

3. Run a scan:
   ```bash
   plexomatic scan --path /path/to/media
   ```

## Contributing

We welcome contributions! Please see our [Contributing Guide](../CONTRIBUTING.md) for details on how to get started.

## Support

If you encounter any issues or have questions:
1. Check the documentation
2. Search existing GitHub issues
3. Create a new issue if needed

## License

This project is licensed under the GPL-2.0 License - see the [LICENSE](../LICENSE) file for details.
