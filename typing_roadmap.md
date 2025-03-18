# Typing Roadmap for Plex-o-matic

This document outlines the plan for gradually adding type annotations to the project.

## Already Typed Files (passing mypy)

These files already have proper type annotations and pass mypy checks:

- `plexomatic/utils/name_parser.py`
- `plexomatic/utils/name_utils.py`
- `plexomatic/core/file_scanner.py`
- `tests/test_name_parser.py`
- `tests/test_name_parser_comprehensive.py`
- `tests/test_file_scanner.py`

## Priority Files for Typing

The following files should be typed next, in priority order:

1. **Core Models & Data Structures**
   - `plexomatic/core/models.py`
     - Issues: `datetime.UTC` usage, need to import from `datetime.timezone`
     - Base class issue needs resolution

2. **Backup System**
   - `plexomatic/core/backup_system.py`
     - Fix return type issues (SQLAlchemy Column types vs Python types)
     - Fix datetime.UTC issue

3. **Config Management**
   - `plexomatic/config/config_manager.py`
     - Fix Optional[str] to Path conversion
     - Fix Any return types

4. **API Clients**
   - `plexomatic/api/tvmaze_client.py`
   - `plexomatic/api/tvdb_client.py`
   - `plexomatic/api/tmdb_client.py`
   - `plexomatic/api/llm_client.py`
   - `plexomatic/api/anidb_client.py`

5. **Metadata System**
   - `plexomatic/metadata/fetcher.py`
   - `plexomatic/metadata/manager.py`

6. **CLI Interface**
   - `plexomatic/cli.py`

7. **Test Files**
   - Prioritize test files for components that have been typed

## Common Issues

1. Missing return type annotations (`-> None`, etc.)
2. Missing parameter type annotations
3. Issues with `Any` return types where more specific types should be used
4. Incorrect handling of Optional/None types
5. SQLAlchemy typing issues (Column vs value)
6. Datetime module usage issues (`datetime.UTC` vs `datetime.timezone.UTC`)

## Migration Strategy

1. Fix one file at a time
2. Add to pre-commit config after fixing
3. Run test suite after each file to ensure functionality
4. Prioritize core components that other parts depend on
