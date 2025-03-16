"""Database models for the backup system."""
from datetime import datetime, UTC
from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class FileRename(Base):
    """Model for tracking file rename operations."""
    
    __tablename__ = "file_renames"
    
    id = Column(Integer, primary_key=True)
    original_path = Column(Text, nullable=False)
    new_path = Column(Text, nullable=False)
    operation_type = Column(String(50), nullable=False)
    checksum = Column(String(64), nullable=False)
    status = Column(String(20), nullable=False, default="pending")
    created_at = Column(DateTime, nullable=False, default=lambda: datetime.now(UTC))
    completed_at = Column(DateTime, nullable=True)
    rolled_back_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        """String representation of the model."""
        return f"<FileRename(id={self.id}, original_path='{self.original_path}', status='{self.status}')>" 