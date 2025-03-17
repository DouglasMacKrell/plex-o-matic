# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
- Updated filename generation to support multi-episode files
- Preview rename functionality now supports multi-episode files

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