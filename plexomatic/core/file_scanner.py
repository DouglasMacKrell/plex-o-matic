"""File scanner module for identifying and analyzing media files."""
import os
import re
from pathlib import Path
from typing import Iterator, List, Set, Optional

class MediaFile:
    """Represents a media file with its properties and metadata."""
    
    def __init__(self, path: Path):
        """Initialize a MediaFile instance.
        
        Args:
            path: Path to the media file
        """
        self.path = Path(path)
        self._analyze_file()
    
    def _analyze_file(self) -> None:
        """Analyze the file to extract basic properties."""
        self.extension = self.path.suffix.lower()
        self.size = self.path.stat().st_size if self.path.exists() else 0
        self.is_multi_episode = bool(re.search(r'E\d+E\d+', self.path.name, re.IGNORECASE))

class FileScanner:
    """Scanner for identifying media files in a directory structure."""
    
    def __init__(
        self,
        base_path: str,
        allowed_extensions: Optional[List[str]] = None,
        ignore_patterns: Optional[List[str]] = None
    ):
        """Initialize a FileScanner instance.
        
        Args:
            base_path: Root directory to scan for media files
            allowed_extensions: List of allowed file extensions (e.g., ['.mp4', '.mkv'])
            ignore_patterns: List of regex patterns for files to ignore
        """
        self.base_path = Path(base_path)
        self.allowed_extensions = set(ext.lower() for ext in (allowed_extensions or []))
        self.ignore_patterns = ignore_patterns or []
    
    def _should_ignore(self, file_path: Path) -> bool:
        """Check if a file should be ignored based on ignore patterns.
        
        Args:
            file_path: Path to check
            
        Returns:
            bool: True if the file should be ignored
        """
        file_name = file_path.name
        return any(re.search(pattern, file_name) for pattern in self.ignore_patterns)
    
    def _is_valid_media_file(self, file_path: Path) -> bool:
        """Check if a file is a valid media file.
        
        Args:
            file_path: Path to check
            
        Returns:
            bool: True if the file is a valid media file
        """
        if not file_path.is_file():
            return False
            
        if self._should_ignore(file_path):
            return False
            
        if self.allowed_extensions and file_path.suffix.lower() not in self.allowed_extensions:
            return False
            
        return True
    
    def scan(self) -> Iterator[MediaFile]:
        """Scan the base directory for media files.
        
        Yields:
            MediaFile: Found media files
        """
        for root, _, files in os.walk(self.base_path):
            for file_name in files:
                file_path = Path(root) / file_name
                
                if self._is_valid_media_file(file_path):
                    yield MediaFile(file_path) 