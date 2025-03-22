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

### MediaType Enum Consolidation

#### Problem Statement
The codebase currently has two separate implementations of the MediaType enum:
1. `plexomatic.utils.name_parser.MediaType` - Uses string values like "tv_show"
2. `plexomatic.core.models.MediaType` - Uses auto-generated integer values from enum.auto()

This duplication creates type incompatibility issues, maintenance burden, cognitive overhead for developers, testing complexity, and documentation confusion.

#### Consolidation Steps

1. **Consolidate to a single MediaType definition**
   - Decide on the preferred implementation (string values are more readable and stable)
   - Create a unified MediaType in a central location (e.g., `plexomatic.core.models`)
   - Ensure the unified enum includes all values from both existing implementations
   - Add proper docstrings and type hints

2. **Add migration code**
   - Create helper functions to convert between old integer values and new string values
   - Add deprecation warnings for the old enum
   - Implement serialization/deserialization logic that handles both formats
   - Consider database migration if enum values are stored in the database

3. **Update all imports**
   - Systematically update all import statements across the codebase
   - Replace all instances of the old enum with the consolidated version
   - Ensure tests use the same enum implementation as the code they test
   - Update any code that directly relies on enum values

4. **Create comprehensive tests**
   - Write tests to verify the new enum works with all existing functionality
   - Add tests for the migration helpers
   - Ensure serialization/deserialization works correctly with both old and new formats
   - Verify backward compatibility with any stored data

#### Implementation Strategy
- Follow test-driven development: write failing tests first
- Implement changes incrementally
- Run the full test suite after each significant change
- Add detailed comments explaining the migration for future developers

### Post-MediaType Consolidation Tasks

#### 1. Address mypy typing issues
- Fix type annotations in compatibility modules
- Address template loading and management type errors
- Resolve Union and Optional type handling
- Update test files with proper type annotations
- Ensure all functions have appropriate return type annotations

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

#### 2. Improve error handling and logging
- Implement proper exception hierarchies
- Add comprehensive error messages
- Ensure all exceptions are properly caught and handled
- Add detailed logging throughout the codebase
- Create standardized logging format

#### 3. Implement comprehensive test fixtures
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
