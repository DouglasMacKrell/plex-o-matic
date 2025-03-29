# Implementation Plan

## Repository Setup and Workflow

### Initial Setup
1. Initialize git repository
2. Create `.gitignore` file
   - Include Python-specific ignores
   - Exclude config files with sensitive data
   - Exclude test media files
3. Create virtual environment
4. Set up pre-commit hooks for code quality

### Branch Strategy
- `main`: Production-ready code
- `develop`: Main development branch
- Feature branches: `feature/feature-name`
- Bugfix branches: `bugfix/bug-description`
- Release branches: `release/v1.x.x`

### Workflow Rules
1. All development happens in feature branches
2. Pull requests required for all merges
3. Version bumping follows semantic versioning
4. Changelog must be updated with each PR
5. Tests must pass before merge

## Phase 1: Foundation (Sprint 1-2)

### 1.1 Project Structure Setup
1. Create directory structure
2. Initialize Python project
3. Set up dependency management
4. Create configuration system

### 1.2 Core File Operations
1. Implement file scanner
   - Directory traversal
   - File type detection
   - Basic metadata extraction
2. Create backup system
   - Database initialization
   - Backup record creation
   - Restore functionality
3. Implement basic CLI
   - Command structure
   - Argument parsing
   - Help system

### 1.3 Testing Framework
1. Set up pytest
2. Create test fixtures
3. Implement unit tests
4. Add integration tests

## Phase 2: API Integration (Sprint 3-4)

### 2.1 API Clients
1. TVDB API integration
   - Client implementation
   - Authentication
   - Rate limiting
   - Caching system
2. TMDB API integration
   - Similar structure to TVDB
3. Local LLM integration
   - Client interface
   - Response parsing
   - Error handling

### 2.2 Metadata Management
1. Implement metadata fetchers
2. Create matching algorithms
3. Add confidence scoring
4. Build caching system

## Phase 3: Advanced Features (Sprint 5-6)

### 3.1 Episode Handling
1. Multi-episode detection
2. Episode concatenation
3. Special episode handling
4. Season pack organization
5. Anthology Show Support
   - Configuration flag for anthology mode
   - Title segment extraction and matching
   - Episode range creation from multiple segments
   - Confidence scoring system
6. Title-Based Matching
   - Implement title vs. episode number priority system
   - Configurable match threshold settings
   - Conflict resolution strategies
7. Directory & Filename Inference
   - Folder structure parsing for series detection
   - Number-only file handling
   - Fallback strategies for incomplete metadata

### 3.2 Name Processing
1. Implement name parser
2. Add LLM-based verification
3. Create name formatter
4. Add template system

### 3.3 Preview System
1. Create preview generator
2. Implement diff display
3. Add batch preview
4. Create interactive approval

## Pre-v2: Code Quality and Refactoring

### Codebase Refactoring
1. Identify areas of technical debt
2. Profile codebase for performance bottlenecks
3. Analyze code complexity and duplication
4. Develop refactoring roadmap for v2

### Name Parser Refactoring
1. Data Model Simplification
   - Split into specific media type classes
   - Remove unnecessary optional fields
   - Implement proper inheritance hierarchy
   - Separate confidence scoring system
2. Pattern Matching Improvements
   - Create pattern registry system
   - Implement pattern priority ordering
   - Add pattern confidence scoring
   - Create pattern testing framework
3. Confidence System Overhaul
   - Define clear confidence levels
   - Document confidence scoring rules
   - Implement consistent scoring system
   - Add confidence validation
4. Modular Processing
   - Create separate parsers per media type
   - Implement parser factory
   - Add parser configuration system
   - Create parser testing framework
5. Code Quality Improvements
   - Reduce regex complexity
   - Implement proper error handling
   - Add comprehensive logging
   - Improve test coverage
6. Performance Optimization
   - Implement pattern caching
   - Add result caching
   - Optimize regex patterns
   - Add performance benchmarks

### Test Suite Improvements
1. Improve test coverage to >90%
2. Add property-based testing
3. Enhance integration tests
4. Add stress testing for edge cases

## Phase 4: UI & Polish (Sprint 7-8)

### 4.1 User Interface
1. Enhance CLI
   - Progress indicators
   - Color coding
   - Interactive mode
2. Add configuration UI
3. Implement batch operations
4. Create status dashboard

### 4.2 Error Handling
1. Implement logging system
2. Add error recovery
3. Create user notifications
4. Implement retry logic

### 4.3 Performance Optimization
1. Add parallel processing
2. Optimize API calls
3. Implement caching
4. Add batch operations

## Testing Strategy

### Unit Tests
- Core functionality
- API clients
- File operations
- Name processing

### Integration Tests
- End-to-end workflows
- API integration
- File system operations
- Database operations

### Performance Tests
- Large directory scanning
- Batch operations
- API response times
- Memory usage

## Documentation

### 1. Code Documentation
- Docstrings
- Type hints
- Architecture diagrams
- API documentation

### 2. User Documentation
- Installation guide
- Configuration guide
- Usage examples
- Troubleshooting guide

### 3. Developer Documentation
- Contributing guide
- Development setup
- API reference
- Architecture overview

## Release Process

### 1. Pre-release
- Version bump
- Changelog update
- Documentation update
- Test suite execution

### 2. Release
- Tag creation
- Package building
- PyPI upload
- Documentation deployment

### 3. Post-release
- Announcement
- Migration guide
- Feedback collection
- Issue tracking

## Maintenance Plan

### Regular Tasks
- Dependency updates
- Security patches
- Performance monitoring
- Bug fixes

### Periodic Reviews
- Code quality
- Test coverage
- Documentation accuracy
- User feedback

### Post-MediaType Consolidation Tasks

#### 1. ✅ Address mypy typing issues (COMPLETED)
- Fixed type annotations in compatibility modules
- Addressed template loading and management type errors
- Resolved Union and Optional type handling
- Updated test files with proper type annotations
- Ensured all functions have appropriate return type annotations
- Added mypy-specific directives where needed
- Fixed safe_cast.py typing issues
- Resolved enum instance attribute access type errors

#### 2. Increase test coverage in low-coverage areas
- Target modules with <70% coverage first
- Focus on refactored template modules (now separated from original name_templates.py)
- Add tests for `plexomatic/utils/safe_cast.py` (0% coverage)
- Improve `plexomatic/utils/media_type_compat.py` coverage
- Follow TDD approach for all new tests
- Create comprehensive type testing

#### 3. Remove deprecated code
- Identify all deprecated code with compatibility layers
- Create migration plan for each deprecated component
- Update documentation for breaking changes
- Implement clean removal of redundant MediaType implementations
- Ensure backward compatibility through proper deprecation notices
- Verify functionality is maintained after removal

### Code Refactoring Tasks

#### 1. ✅ Split name_templates.py into manageable modules (COMPLETED)
- Original file was over 1200 lines with complex functionality
- Successfully broken down into smaller, focused modules:
  - `template_types.py`: Enums, constants, and helper functions
  - `template_manager.py`: Template loading and management
  - `template_formatter.py`: Core formatting functionality
  - `multi_episode_formatter.py`: Multi-episode handling
  - `default_formatters.py`: Media type-specific default formatters
  - `template_registry.py`: Public API for template registration
  - `file_utils.py`: High-level utilities for file operations
- Implemented clean interfaces between modules
- Fixed existing syntax and type errors during refactoring
- Used proper type annotations throughout
- Eliminated duplicated code
- Implemented comprehensive unit tests for each module
- Complete test coverage for most modules

#### 2. ✅ Standardize testing approach using pytest (COMPLETED)
- Identified mix of unittest and pytest testing approaches
- Standardized on pytest for:
  - Simpler syntax (plain assert statements)
  - Powerful fixture system
  - Better parametrization support
  - Extensive plugin ecosystem
- Migration plan:
  - Converted unittest-style tests to pytest style
  - Moved tests from /tests/unit to appropriate directories in main test structure
  - Updated test fixtures for reusability
  - Ensured consistent testing patterns across the codebase
  - Improved test documentation
  - Added parametrized tests where appropriate
  - Maintained or improved test coverage during migration
  - Removed non-functional skipped tests, replacing with TODO comments
- Completed migrations:
  - ✅ Migrated TVDB client tests from unittest to pytest
  - ✅ Verified pytest-style episode detector tests
  - ✅ Created migration plan document (pytest_migration_plan.md)
  - ✅ Migrated episode parser, formatter, and consolidated media type tests to pytest
  - ✅ Migrated episode handler tests to pytest
  - ✅ Fixed CLI import issues in tests
  - ✅ Fixed format expectations in `format_multi_episode_filename` test
  - ✅ Fixed `NameParser.use_llm` test to match implementation
  - ✅ Documented remaining test failures that need to be addressed

**Migration Completed**:
- ✅ Migrated TVDB client tests from unittest to pytest
- ✅ Verified pytest-style episode detector tests
- ✅ Created migration plan document (pytest_migration_plan.md)
- ✅ Migrated episode parser, formatter, and consolidated media type tests to pytest
- ✅ Migrated episode handler tests to pytest
- ✅ Fixed CLI import issues in tests
- ✅ Fixed format expectations in `format_multi_episode_filename` test
- ✅ Fixed `NameParser.use_llm` test to match implementation
- ✅ Documented remaining test failures that need to be addressed

**Current Test Status**:
- 509 passing tests
- 0 failing tests
- 51 skipped tests

**Next Steps**:
1. ✅ Fix `process_anthology_episode()` parameter mismatch issues
2. ✅ Update file operation tests to work with temporary files
3. ✅ Fix integration tests that expect dots instead of spaces
4. ✅ Address the missing `detect_segments_with_llm` function
5. ✅ Fix the preview generator directory test mismatch
6. ✅ Fix formatter functions to correctly handle colons in different formatting styles
7. ✅ Fix parser extract_show_info function to return empty dict instead of None
8. ✅ Set default value of concatenated parameter to True in format_multi_episode_filename

These issues will be addressed in a follow-up PR to maintain a clean and focused approach to the migration.

#### 3. Improve error handling and logging
- Implement proper exception hierarchies
- Add comprehensive error messages
- Ensure all exceptions are properly caught and handled
- Add detailed logging throughout the codebase
- Create standardized logging format

#### 4. Implement comprehensive test fixtures
- Create fixture factories for common test objects
- Implement property-based testing for complex functions
- Add test coverage for edge cases and error conditions
- Create test utilities for common testing patterns

## Timeline
- Phase 1: Weeks 1-4
- Phase 2: Weeks 5-8
- Phase 3: Weeks 9-12
- Phase 4: Weeks 13-16
- Testing & Documentation: Ongoing
- First Release (v1): Week 16
- Pre-v2 Refactoring: Weeks 17-20
- V2 Development: Weeks 21-28
- Maintenance: Ongoing

## Current Sprint: Post-MVP Refinement

### Immediate Next Steps
1. ✅ Code Refactoring: Break Up Monolithic Files (COMPLETED)
   - Created a dedicated refactoring branch from current state
   - Fixed syntax error in episode_handler.py line 366 (incorrect else clause indentation)
   - Split episode_handler.py (1,800+ lines) into focused modules:
     - `episode_parser.py` - Functions for extracting information from filenames
     - `episode_formatter.py` - Functions for formatting episode filenames
     - `detector.py` - Episode detection logic (renamed from segment_detector.py)
     - `processor.py` - High-level episode processing logic
   - Ensured consistent function signatures across modules
   - Addressed test failures as part of the refactoring process
   - Followed TDD approach when rewriting functionality
   - Improved test coverage (from 4% for episode_handler.py)
   - Fixed API inconsistencies (e.g., process_anthology_episode parameter issues)
   - Improved imports to avoid circular dependencies
   - Added function/module documentation
   - Ensured all exported functionality remains available through compatibility layer
   - Made incremental commits for each logical module extraction
   - Applied consistent code formatting and readability improvements
   - Fixed whitespace and line endings across the codebase
   - Ensured proper spacing between functions and classes
   - Applied consistent indentation for multi-line statements
   - Fixed type errors found by mypy:
     - Added proper type annotations to functions and variables
     - Fixed unreachable code issues detected by static analysis
     - Made null checks more consistent and robust
     - Corrected parameter and return type annotations
   - Addressed ruff linting issues:
     - Resolved comparison issues (using `is True` instead of `== True`)
     - Fixed undefined names by adding missing imports
     - Eliminated unused variables

2. ✅ Clean up and Finalize Current Branch (COMPLETED)
   - Fixed all remaining tests with the new modular architecture
   - Ensured pre-commit hooks pass
   - Updated CHANGELOG.md with improvements
   - Updated PLAN.md to reflect current progress
   - Committed, pushed, and merged work

3. API Integration Verification
   - Test all existing API clients (TVDB, TMDB, AniDB, TVMaze, LLM)
   - Implement MusicBrainz API client for music metadata
   - Run practical test sweep to verify no 4XX errors
   - Ensure proper rate limiting and error handling
   - Implement comprehensive caching to minimize API calls

4. Media Type Determination Improvement
   - Replace simplistic filename pattern matching with robust detection
   - Use API clients to verify and refine media type detection
   - Implement confidence scoring for media type determination
   - Use LLM to help with ambiguous cases
   - Create fallback strategies for uncertain cases

5. Metadata-Driven Naming System
   - Use API responses to drive filename formatting
   - Align with Plex metadata agent expectations
   - Implement proper handling for all supported media types
   - Create robust validation for generated filenames
   - Build testable, reliable metadata extraction system

### Progress So Far
1. ✅ Template System Refactoring Complete
   - Split large name_templates.py module into smaller, focused modules
   - Enhanced test coverage with dedicated test files
   - Fixed circular dependencies and improved code organization
   - All tests passing with proper type annotations

2. ✅ Preview System Implementation
   - Core preview functionality in plexomatic/utils/preview_system.py
   - Preview commands in CLI interface
   - Diff display for file operations
   - Batch preview capabilities

3. ✅ Configuration System
   - Interactive CLI configuration for API keys
   - Secure storage of credentials
   - LLM integration settings

4. ✅ CLI Command Implementation
   - Implemented `templates` command with `list` and `show` subcommands
   - Added template preview functionality
   - Enhanced test coverage for CLI commands
   - Fixed type errors in template formatter
   - Ensured all tests pass with proper type annotations

5. ✅ Documentation Overhaul
   - Created comprehensive Getting Started guide
   - Updated existing documentation
   - Added template system documentation
   - Improved navigation between documentation sections
   - Enhanced README with detailed usage examples

6. ✅ Package Publication
   - Set up PyPI project
   - Published package to PyPI
   - Created GitHub Actions workflow for automated publishing
   - Made package installable via pip

7. ✅ Code Quality and Testing
   - Integrated Codecov for coverage reporting
   - Set up GitHub Actions for automated testing
   - Fixed code formatting and linting issues
   - Maintained high code quality through pre-commit hooks
   - Fixed all failing tests related to episode formatting and parsing
   - Fixed issues with multi-episode filename formatting
   - Improved character handling in episode titles and show names

### Specific Technical Tasks

#### 1. Implement MusicBrainz API Client
- Create `plexomatic/api/musicbrainz_client.py`
- Implement artist, album, and track search functions
- Add comprehensive error handling
- Implement rate limiting and caching
- Write unit tests following TDD approach
- Document API endpoints and response formats
- Add integration with existing media type detection

#### 2. Media Type Detection Refactoring
- Create unified `MediaTypeDetector` class
- Implement multi-stage detection pipeline:
  1. Initial pattern-based detection
  2. API verification when pattern detection is uncertain
  3. LLM assistance for highly ambiguous cases
- Add confidence scoring for each detection method
- Implement comprehensive logging of detection steps
- Create test fixtures for various media types

#### 3. Refactor `episode_handler.py`
- Split into smaller, focused modules
- Create proper separation of concerns
- Improve error handling and logging
- Add comprehensive type annotations
- Fix mypy errors
- Increase test coverage
- Implement proper API integration

#### 4. Metadata-to-Filename Bridge
- Create unified system for converting API metadata to Plex-compatible filenames
- Implement media-type-specific formatters
- Add validation for generated filenames
- Ensure compliance with Plex naming conventions
- Create test suite for various edge cases

## Code Cleanup Phase (Before API Integration)

### 1. Resolve Code Duplication
- ✅ Remove duplicate episode_detector.py implementation (COMPLETED)
  - ✅ Compared functionality between utils/episode_detector.py and utils/episode/episode_detector.py
  - ✅ Consolidated into a single implementation with complete test coverage
  - ✅ Updated all imports to use the canonical path
  - ✅ Added deprecation warnings to maintain backward compatibility
  - ✅ Fixed multi-episode range detection and segment counting issues
  - ✅ Improved logging throughout the detector module
  - ✅ Created proper tests for all episode detection functionality
- ✅ Clean up deprecated MediaType compatibility layers (COMPLETED)
  - ✅ Identified all instances of MediaType enums across the codebase
  - ✅ Removed deprecated implementations in core.models and metadata.fetcher
  - ✅ Deleted the compatibility layer in utils.media_type_compat
  - ✅ Updated all imports to reference the consolidated version from core.constants
  - ✅ Updated tests to verify proper MediaType usage
  - ✅ Added entries to CHANGELOG.md to document the changes

### 2. Refactor Large Files
- Split fetcher.py into modules by metadata source
  - Create dedicated modules for each metadata fetcher
  - Maintain backward compatibility with the original API
  - Improve test coverage for each component
- Refactor name_parser.py into focused sub-modules
  - Separate media type detection, TV parsing, movie parsing, anime parsing
  - Create a clean public API that maintains backward compatibility
  - Improve type annotations and error handling
- Break down preview_system.py into component modules
  - Separate preview generation, diff display, and user interaction
  - Create modular components with clean interfaces
  - Enhance test coverage for each component

### 3. Documentation Updates
- Document refactored episode handling modules
  - Update API documentation for all public functions
  - Add usage examples for common scenarios
  - Create diagrams to illustrate component relationships
- Complete missing documentation in docs/ directory
  - Fill in placeholder README.md files
  - Add detailed guides for each major feature
  - Create troubleshooting sections for common issues
- Update template system documentation for modular structure
  - Document the new template components and their relationships
  - Add examples of custom template creation
  - Create a quick reference for template syntax

### 4. API Integration Tasks
   a. API Client Testing (feature/api-client-testing)
      - ✅ Test all existing API clients (TVDB, TMDB, AniDB, TVMaze, LLM)
      - ✅ Create comprehensive test suite for TVMaze client
      - ✅ Implement modular test structure for TVMaze:
        - ✅ Core client functionality and error handling tests
        - ✅ Search functionality tests (shows and people)
        - ✅ Show and episode details retrieval tests
        - ✅ Mocking patterns for use in integration tests
      - ✅ Achieve >95% test coverage for TVMaze client (currently 98%)
      - ✅ Document TVMaze API client usage patterns
      - ✅ Add proper error handling and logging for TVMaze client
      - ✅ Standardize tests on pytest instead of unittest
      - ✅ Organize test files into structured directories
      - ✅ Document any issues found
      - ✅ Add proper error handling and logging
      - ✅ Follow TDD approach for all new tests
      - ✅ Ensure backward compatibility
      - ✅ Add integration tests for each client

   b. MusicBrainz Integration (feature/musicbrainz-integration)
      - Create plexomatic/api/musicbrainz_client.py
      - Implement artist, album, and track search functions
      - Add comprehensive error handling
      - Write unit tests following TDD approach
      - Document API endpoints and response formats
      - Add integration with existing media type detection
      - Ensure proper rate limiting compliance

   c. API Error Handling (feature/api-error-handling)
      - Run practical test sweep to verify no 4XX errors
      - Implement proper error handling for all API responses
      - Add retry mechanisms for transient failures
      - Create error reporting system
      - Add logging for API errors
      - Implement graceful degradation
      - Add error recovery strategies

   d. API Rate Limiting (feature/api-rate-limiting)
      - Implement rate limiting for all API clients
      - Add rate limit tracking and backoff strategies
      - Create rate limit configuration system
      - Add tests for rate limiting behavior
      - Document rate limit policies
      - Implement rate limit monitoring
      - Add rate limit statistics

   e. API Caching (feature/api-caching)
      - Implement comprehensive caching system
      - Add cache invalidation strategies
      - Create cache configuration options
      - Add cache statistics and monitoring
      - Implement cache persistence
      - Add cache warming capabilities
      - Create cache debugging tools
