# Database Schema Documentation

## Overview

Plex-o-matic uses SQLite as its database engine, providing a lightweight, serverless solution for tracking file operations and system state. The database is designed to ensure data integrity and provide a complete audit trail of all file operations.

## Tables

### 1. FileOperations

Tracks all file operations performed by the system.

```sql
CREATE TABLE file_operations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    original_path TEXT NOT NULL,
    new_path TEXT NOT NULL,
    operation_type TEXT NOT NULL,
    checksum TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    rolled_back_at TIMESTAMP,
    status TEXT NOT NULL DEFAULT 'pending'
);
```

#### Columns:
- `id`: Unique identifier for each operation
- `original_path`: Source path of the file
- `new_path`: Destination path for the file
- `operation_type`: Type of operation (e.g., 'move', 'rename', 'copy')
- `checksum`: File checksum for integrity verification
- `created_at`: Timestamp when operation was recorded
- `completed_at`: Timestamp when operation was completed
- `rolled_back_at`: Timestamp if operation was rolled back
- `status`: Current status ('pending', 'completed', 'rolled_back', 'failed')

#### Indexes:
- Primary key on `id`
- Index on `status` for quick status queries
- Index on `created_at` for temporal queries

### Future Tables

#### 1. MediaMetadata (Planned)
```sql
CREATE TABLE media_metadata (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    file_path TEXT NOT NULL UNIQUE,
    title TEXT,
    year INTEGER,
    type TEXT,  -- movie, tv_show, etc.
    tmdb_id TEXT,
    tvdb_id TEXT,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);
```

#### 2. ConfigurationHistory (Planned)
```sql
CREATE TABLE configuration_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    config_key TEXT NOT NULL,
    config_value TEXT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    active BOOLEAN NOT NULL DEFAULT TRUE
);
```

## Data Integrity

### Constraints
1. All timestamps use UTC timezone
2. Required fields are marked as NOT NULL
3. Status field limited to predefined values
4. Checksums stored for file verification

### Transactions
- File operations are wrapped in transactions
- Rollbacks maintain database consistency
- Concurrent access handled via SQLite's locking

## Backup and Maintenance

### Backup Strategy
1. Database file backed up before major operations
2. Regular automated backups recommended
3. Backup rotation to manage storage

### Maintenance Tasks
1. Regular VACUUM to reclaim space
2. Index optimization
3. Cleanup of old records (configurable retention)

## Usage Examples

### Query Recent Operations
```sql
SELECT
    id,
    original_path,
    new_path,
    operation_type,
    status,
    created_at
FROM file_operations
WHERE created_at >= datetime('now', '-1 day')
ORDER BY created_at DESC;
```

### Check Failed Operations
```sql
SELECT
    id,
    original_path,
    new_path,
    operation_type,
    created_at
FROM file_operations
WHERE status = 'failed'
ORDER BY created_at DESC;
```

### Rollback History
```sql
SELECT
    id,
    original_path,
    new_path,
    rolled_back_at
FROM file_operations
WHERE rolled_back_at IS NOT NULL
ORDER BY rolled_back_at DESC;
```
