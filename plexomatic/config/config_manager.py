"""Configuration manager for Plex-o-matic."""
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional

class ConfigManager:
    """Manager for loading, saving, and accessing configuration settings."""
    
    DEFAULT_CONFIG = {
        "db_path": "~/.plexomatic/plexomatic.db",
        "log_level": "INFO",
        "allowed_extensions": [".mp4", ".mkv", ".avi", ".mov", ".m4v"],
        "ignore_patterns": ["sample", "trailer", "extra"],
        "recursive_scan": True,
        "backup_enabled": True,
    }
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the configuration manager.
        
        Args:
            config_path: Path to the configuration file, or None to use default
        """
        self.config_path = Path(config_path or os.environ.get(
            "PLEXOMATIC_CONFIG_PATH", 
            "~/.plexomatic/config.json"
        )).expanduser()
        self.config: Dict[str, Any] = dict(self.DEFAULT_CONFIG)
        self.load()
    
    def load(self) -> None:
        """Load configuration from file.
        
        If the configuration file doesn't exist, create it with default values.
        """
        if not self.config_path.exists():
            # Create directory if it doesn't exist
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            # Save default config
            self.save()
            return
            
        try:
            with open(self.config_path, "r") as f:
                loaded_config = json.load(f)
                self.config.update(loaded_config)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading configuration: {e}")
            # Use defaults if loading fails
            # Also save the default config to fix the invalid file
            self.save()
    
    def save(self) -> None:
        """Save current configuration to file."""
        try:
            # Ensure directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(self.config_path, "w") as f:
                json.dump(self.config, f, indent=4)
        except IOError as e:
            print(f"Error saving configuration: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key doesn't exist
            
        Returns:
            Any: Configuration value
        """
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set a configuration value.
        
        Args:
            key: Configuration key
            value: Configuration value
        """
        self.config[key] = value
        self.save()
    
    def get_db_path(self) -> Path:
        """Get the database path.
        
        Returns:
            Path: Path to the database file
        """
        return Path(self.get("db_path", "~/.plexomatic/plexomatic.db")).expanduser()
    
    def get_allowed_extensions(self) -> list:
        """Get allowed file extensions.
        
        Returns:
            list: List of allowed file extensions
        """
        return self.get("allowed_extensions", [".mp4", ".mkv", ".avi", ".mov", ".m4v"])
    
    def get_ignore_patterns(self) -> list:
        """Get patterns to ignore.
        
        Returns:
            list: List of patterns to ignore
        """
        return self.get("ignore_patterns", ["sample", "trailer", "extra"]) 