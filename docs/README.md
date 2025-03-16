# Plex-o-matic Documentation

Welcome to the Plex-o-matic documentation. This guide will help you understand how to use and get the most out of Plex-o-matic for organizing your media files.

## Table of Contents

- [Getting Started](#getting-started)
- [Usage Guide](#usage-guide)
- [Documentation Sections](#documentation-sections)
- [FAQs](#faqs)

## Getting Started

Plex-o-matic is a powerful tool designed to help you organize your media files for Plex. It automates the process of scanning, renaming, and organizing media files according to Plex's preferred naming conventions.

### Installation

```bash
pip install plex-o-matic
```

## Usage Guide

Once installed, you can use Plex-o-matic via the command line interface:

```bash
plexomatic scan --path /path/to/your/media
```

For more detailed usage instructions, please refer to the [CLI Documentation](cli/README.md).

## Documentation Sections

- [CLI Documentation](cli/README.md): Detailed information on using the command line interface.
- [Backend Architecture](backend/README.md): Information about the backend design and components.
- [Database Schema](database/README.md): Documentation on the database structure and schema.

## FAQs

### How does Plex-o-matic handle existing files?

Plex-o-matic uses a backup system to keep track of all file operations. This ensures that any changes made can be rolled back if needed.

### Can I use Plex-o-matic with existing Plex installations?

Yes, Plex-o-matic is designed to work with existing Plex installations and follows Plex's naming conventions. 