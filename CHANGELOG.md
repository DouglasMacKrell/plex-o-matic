# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Subtitle file detection and handling:
  - Added SubtitleFile class for subtitle representation
  - Implemented automatic language detection from filenames
  - Support for "forced" and "SDH" subtitle types
  - Added matching algorithm to pair subtitles with media files
  - Implemented Plex-compatible subtitle renaming
  - Added comprehensive test suite for subtitle functionality
  - Created detailed documentation for subtitle support

### Changed
- None

### Deprecated
- None

### Removed
- None

### Fixed
- None

### Security
- None

## [0.3.0] - 2024-06-21

### Added
- API Integration Package
  - TVDB API client with authentication, caching, and rate limiting
    - Supports search for TV series by name
    - Retrieves series details and episode information
    - Token management and automatic refresh
    - Request caching for better performance
  - TMDB API client with configuration, search, and details functionality
  - AniDB API client with UDP/HTTP combined access for anime metadata
    - Combined UDP and HTTP API access
    - Anime search and metadata retrieval
    - Episode information with titles
    - Rate limiting and session management
  - TVMaze API client with comprehensive show and person data
    - Show search by name and retrieval by ID
    - Episode information and specific episode lookup
    - Cast information for shows
    - People search functionality
    - Efficient caching and rate limiting
  - Local LLM client using Ollama with Deepseek R1 8b
  - Media metadata analysis and filename suggestions
  - Comprehensive test suite for all API clients
- Metadata Management System
  - MetadataManager for aggregating results from multiple sources
  - Unified search interface across all metadata providers
  - Intelligent filename matching and metadata extraction
  - Confidence-based result ranking
  - Efficient caching mechanism
  - Customizable match threshold
  - Text similarity scoring for better matching
  - Comprehensive test coverage
  - Enhanced metadata-episode integration
    - Special episode metadata retrieval and formatting
    - Multi-episode metadata handling for sequential and non-sequential episodes
    - Improved match detection for episode types
    - Support for various episode naming conventions
- Interactive CLI Configuration
  - New `configure` command for interactive API key setup
  - Securely stores API keys and other settings
  - Guides users through setup process for all API services
  - Support for optional services configuration
  - Test coverage for all configuration scenarios
- Enhanced episode handling:
  - Multi-episode detection with support for various formats (S01E01E02, S01E01-E02, etc.)
  - Episode range parsing with limits for very large ranges
  - Special episode detection (OVAs, specials, movies)
  - Season pack organization functionality
  - Support for concatenated episodes (non-sequential episodes in one file)
  - Intelligent filename generation from metadata for all episode types
  - Anthology show support with configurable mode
    - Title-based episode matching with confidence scoring
    - Directory structure inference for incomplete metadata
    - Configurable title vs. episode number priority
    - Enhanced metadata integration for anthology shows
  - Improved episode title matching system
    - Fuzzy matching for episode titles
    - Configurable confidence thresholds
    - Intelligent episode number override based on title matches
- Updated filename generation to support multi-episode files
- Preview rename functionality now supports multi-episode files
- Template System for Media File Names
  - Customizable templates for TV shows, movies, and anime
  - Support for special episodes and different media types
  - Template registration and management system
  - Default templates for common naming formats (Plex, Kodi, etc.)
  - Template application with format string parsing
- Preview System
  - Advanced preview generator for showing proposed changes
  - Interactive diff display for file operations
  - Batch preview functionality for multiple files
  - Interactive approval system for changes
- CLI Template Commands
  - New `templates` command with `list` and `show` subcommands
  - Interactive template preview functionality
  - Support for viewing all registered templates
  - Enhanced test coverage for all template commands
- Comprehensive Documentation
  - Getting Started guide with step-by-step instructions
  - Template System documentation
  - Command reference for all CLI operations
  - Troubleshooting section with common issues and solutions

### Changed
- Completed refactoring of the template system:
  - Split large name_templates.py module (1200+ lines) into smaller, focused modules
  - Created new modules: template_types.py, template_manager.py, template_formatter.py,
    multi_episode_formatter.py, default_formatters.py, template_registry.py, and file_utils.py
  - Improved type annotations and docstrings throughout
  - Enhanced test coverage with dedicated test files for each module
  - Fixed circular dependencies and improved code organization
  - Added clear interfaces between modules
- Improved MediaType enum compatibility and consolidation:
  - Created type-safe compatibility layers for existing MediaType implementations
  - Fixed attribute access on enum instances with proper type annotations
  - Enhanced backward compatibility between core, parser, and fetcher MediaType variants
  - Added type variables and improved generics for better static analysis
- Enhanced template formatting system:
  - Added `get_default_template` function for consistent template defaults
  - Implemented support for multi-episode formatting in template strings
  - Created template directory structure for future customization
  - Fixed type issues in template formatter functions
  - Added proper deprecation warnings for obsolete functions
  - Improved test compatibility with mocking support
  - Added proper handling for special test cases

### Deprecated
- None

### Removed
- Removed name_templates.py after completing refactoring into smaller modules
- Removed redundant backup test files that were moved to proper locations
- Removed temporary helper scripts (move_tests.py and check_syntax.py) that were used during refactoring

### Fixed
- Comprehensive type annotation improvements for test files
  - Added mypy type checking with `--disallow-untyped-defs` for all test files
  - Fixed type annotations in test mocks and fixtures
  - Created properly typed conftest.py for pytest fixtures
- Fixed failing tests in metadata manager
  - Improved mocking strategy for MetadataManager.fetch_metadata
  - Added proper error handling for invalid IDs
  - Enhanced test coverage for edge cases
- Removed unused variables in test files
- Improved code quality throughout test codebase
- Added typing_roadmap.md to track typing progress
- Fixed various mypy typing issues:
  - Improved type annotations in safe_cast.py with proper generic support
  - Fixed typing in the template system and formatter modules
  - Added proper typing for the multi-episode formatter
  - Resolved MediaType enum typing issues across multiple modules
  - Added mypy-specific directives where needed for compatibility with older Python versions
  - Ensured type-safe instance attribute access on enum instances
- Fixed template formatter tests:
  - Resolved test failures in multi-episode formatting
  - Fixed template application with proper error handling
  - Ensured consistent behavior in template registry functionality
  - Added comprehensive test cases for all template formatter functions
  - Fixed inconsistencies between test files and implementation

### Security
- None

## [0.2.0] - 2024-03-21

### Added
- GitHub Actions workflows for CI/CD
  - Automated testing on Python 3.8-3.11
  - Code quality checks (black, ruff, mypy)
  - Code coverage reporting with Codecov
  - Automated releases to GitHub and PyPI
- Mypy configuration for strict type checking
- Command Line Interface (CLI) implementation
  - Main CLI entry point with version display
  - Scan command for finding media files
  - Preview command for showing proposed changes
  - Apply command for making changes with confirmation
  - Rollback command for reverting changes
  - Verbose output option for detailed logging
- Configuration system for managing application settings
  - Default configuration with customizable options
  - Environment variable support
  - Helper methods for common configuration values
- File name utilities for standardizing media filenames
  - TV show and movie filename pattern detection
  - Standardized filename generation
  - Preview of proposed file renames
- File operations with backup support
  - Safe file renaming with checksum verification
  - Operation tracking in database
  - Rollback capability for all operations
- Comprehensive documentation
  - CLI usage and options
  - Configuration system
  - File utilities
  - Core architecture

### Changed
- Enhanced FileScanner with recursive option to control directory traversal depth
- Updated datetime usage to timezone-aware objects for better compatibility
- Connected CLI commands to actual functionality for file operations

### Deprecated
- None

### Removed
- None

### Fixed
- Fixed confirmation prompts in CLI commands for automated testing
- Fixed version display format in CLI output
- Fixed verbose mode output for better test capture and user feedback

### Security
- None

## [0.1.0] - 2024-03-19

### Added
- Comprehensive documentation
  - Backend architecture documentation
  - Database schema documentation
  - Main documentation index
  - Quick start guide
  - Usage examples and code snippets
- Backup system implementation
  - SQLite database integration with SQLAlchemy
  - File operation tracking and history
  - Operation status management (pending, completed, rolled back)
  - Checksum verification for safe rollbacks
  - Comprehensive test suite for backup functionality
- Core file scanner module
  - Basic file scanning functionality
  - Media file detection and analysis
  - Multi-episode file detection
  - System file ignoring
- Test infrastructure
  - Added pytest configuration
  - Created initial test suite for file scanner
  - Added test dependencies
- Initial project setup
  - Created project structure with core modules
  - Added pyproject.toml with initial dependencies
  - Created example configuration file
  - Set up virtual environment
  - Added README.md with installation and usage instructions
- Created SPEC.md with comprehensive project specifications
- Created PLAN.md with detailed implementation plan
- Created CHANGELOG.md for tracking project history
- Basic repository structure definition
- Set up Git workflow with main and develop branches

### Changed
- Updated pyproject.toml with test and development dependencies

### Deprecated
- None

### Removed
- None

### Fixed
- None

### Security
- None
