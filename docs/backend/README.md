![Plex-O-Matic Title Image](../../public/Plex-O-Matic_README_Title_Image.webp)

# Backend Documentation

Plex-o-matic's backend system provides a robust foundation for managing media files with safety and reliability.

## Components

The backend consists of several interconnected components:

- **File Scanner**: Discovers and analyzes media files in your filesystem
- **Backup System**: Provides safe file operations with rollback capability
- **Database Layer**: Maintains operation history and system state
- **Configuration System**: Manages application settings

## Architecture

For detailed information about the backend architecture, refer to the [Architecture Documentation](architecture.md).

## Safe File Operations

All file operations in Plex-o-matic are designed with safety in mind:

1. Operations are recorded in the database before execution
2. Checksum verification ensures file integrity
3. Failed operations can be automatically rolled back
4. Operation history provides a complete audit trail

## Integration Points

The backend integrates with:

- **Metadata APIs**: TVDB, TMDB, AniDB, and TVMaze for media information
- **Local LLM**: Optional AI-powered name recognition for complex media files
- **Plex API**: Integration for media library management

## Error Handling

The backend includes comprehensive error handling:

- Graceful failure recovery
- Detailed error logging
- Operation validation before execution
- Validation of required API credentials

## Development

When extending the backend, follow these guidelines:

1. All file operations must use the BackupSystem
2. Transaction safety for database operations
3. Proper error handling and logging
4. Test coverage for all new functionality
