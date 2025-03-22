"""Database models for the backup system."""

from datetime import datetime, timezone
from enum import Enum, auto
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.orm import declarative_base
from typing import Any, TypeVar
import warnings

# Import the consolidated MediaType
from plexomatic.core.constants import MediaType as ConsolidatedMediaType

# Create the declarative base
Base = declarative_base()

# Type variable for SQLAlchemy models
T = TypeVar("T", bound=Any)


# Deprecated - kept for backward compatibility
class MediaType(Enum):
    """Enum representing types of media.
    
    DEPRECATED: Use plexomatic.core.constants.MediaType instead.
    This class is kept for database backward compatibility.
    """

    TV_SHOW = auto()
    MOVIE = auto()
    ANIME = auto()
    TV_SPECIAL = auto()
    ANIME_SPECIAL = auto()
    UNKNOWN = auto()

    @classmethod
    def from_string(cls, value: str) -> "MediaType":
        """Convert a string value to a MediaType enum value.

        This is used for compatibility between different enum implementations.
        """
        warnings.warn(
            "models.MediaType is deprecated. Use constants.MediaType instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        
        value = value.upper()
        for member in cls:
            if member.name == value:
                return member
        return cls.UNKNOWN
    
    def to_consolidated(self) -> ConsolidatedMediaType:
        """Convert to the consolidated MediaType."""
        return ConsolidatedMediaType.from_legacy_value(self.value, "core")


# Type to help with type checking
class FileRename(Base):  # type: ignore
    """Model for tracking file rename operations."""

    __tablename__ = "file_renames"

    id = Column(Integer, primary_key=True)
    original_path = Column(Text, nullable=False)
    new_path = Column(Text, nullable=False)
    operation_type = Column(String(50), nullable=False)
    checksum = Column(String(64), nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    completed_at = Column(DateTime, nullable=True)
    rolled_back_at = Column(DateTime, nullable=True)

    def __repr__(self) -> str:
        """String representation of the model."""
        return f"<FileRename(id={self.id}, original_path='{self.original_path}', status='{self.status}')>"


class BackupEntry(Base):  # type: ignore
    """Model for storing backup entries."""

    __tablename__ = "backup_entries"

    id = Column(Integer, primary_key=True)
    original_path = Column(String, nullable=False)
    backup_path = Column(String, nullable=False)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    operation = Column(String, nullable=False)
    status = Column(String, nullable=False)
    details = Column(Text, nullable=True)

    def __repr__(self) -> str:
        """Return string representation of the backup entry."""
        return (
            f"BackupEntry(id={self.id}, "
            f"original_path='{self.original_path}', "
            f"backup_path='{self.backup_path}', "
            f"timestamp='{self.timestamp}', "
            f"operation='{self.operation}', "
            f"status='{self.status}')"
        )


class ConfigEntry(Base):  # type: ignore
    """Model for storing configuration entries."""

    __tablename__ = "config_entries"

    id = Column(Integer, primary_key=True)
    section = Column(String, nullable=False)
    key = Column(String, nullable=False)
    value = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self) -> str:
        """Return string representation of the config entry."""
        return (
            f"ConfigEntry(id={self.id}, "
            f"section='{self.section}', "
            f"key='{self.key}', "
            f"value='{self.value}', "
            f"timestamp='{self.timestamp}')"
        )
