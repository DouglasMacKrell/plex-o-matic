![Plex-O-Matic Title Image](../../public/Plex-O-Matic_README_Title_Image.webp)

# Database Documentation

Plex-o-matic uses SQLite as its database engine, providing a lightweight yet powerful solution for data persistence.

## Core Features

- **Zero Configuration**: SQLite requires no setup or server processes
- **Cross-Platform**: Works identically across all supported operating systems
- **Reliability**: Transaction-based operations ensure data integrity
- **Performance**: Optimized for media library management operations

## Schema

The database schema includes tables for:

- File operations tracking
- Media metadata storage
- Configuration history
- Backup management

For detailed schema information, see the [Schema Documentation](schema.md).

## ORM Integration

Plex-o-matic uses SQLAlchemy as its ORM (Object-Relational Mapping) layer:

- Models defined in `plexomatic.core.models`
- Type-safe database operations
- Automatic schema migrations
- Connection pooling for performance

## Example Usage

```python
from plexomatic.core.models import MediaFile, Session

# Create a session
with Session() as session:
    # Query for media files
    media_files = session.query(MediaFile).filter(
        MediaFile.media_type == "TV_SHOW"
    ).all()

    # Process files
    for media_file in media_files:
        print(f"{media_file.name} - Season {media_file.season}")
```

## Migrations

Database schema changes are managed through migrations:

1. Migrations are located in `plexomatic/core/migrations`
2. Automatic upgrade on application startup
3. Version tracking prevents inconsistent states

## Backup and Recovery

The database is automatically backed up:

- Before schema migrations
- On user request via the CLI
- According to the configured backup schedule

## Development Guidelines

When working with the database:

1. Always use transactions for data modifications
2. Create migrations for schema changes
3. Use type annotations and validation
4. Include appropriate indices for performance
5. Write tests for database operations
