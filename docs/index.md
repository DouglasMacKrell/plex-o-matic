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

## Quick Start

1. Install the package:
   ```bash
   pip install plex-o-matic
   ```

2. Create a configuration file:
   ```bash
   plexomatic init
   ```

3. Edit the configuration file at `~/.plexomatic/config.yaml`

4. Run a scan:
   ```bash
   plexomatic scan
   ```

## Contributing

We welcome contributions! Please see our [Contributing Guide](../CONTRIBUTING.md) for details on how to get started.

## Support

If you encounter any issues or have questions:
1. Check the documentation
2. Search existing GitHub issues
3. Create a new issue if needed

## License

This project is licensed under the MIT License - see the [LICENSE](../LICENSE) file for details. 