"""
Hamilton Configuration Loader

This module provides utilities for loading and accessing configuration from .properties files.
It supports environment-specific configuration and overrides from environment variables.
"""

import configparser
import os
import re
from pathlib import Path
from typing import Any, Dict, Optional


class ConfigLoader:
    """Loads and provides access to Hamilton configuration from .properties files."""

    def __init__(self, config_dir: Optional[str] = None):
        """Initialize the config loader.

        Args:
            config_dir: Directory containing configuration files. If None, uses the 'config'
                directory relative to the current working directory.
        """
        if config_dir is None:
            # Default to the 'config' directory in the project root
            self.config_dir = Path(os.path.dirname(os.path.abspath(__file__)))
        else:
            self.config_dir = Path(config_dir)

        # Load the main configuration
        self.main_config = self._load_properties_file("hamilton.properties")
        
        # Load environment-specific configuration
        self.env_config = self._load_properties_file("environment.properties")
        
        # Determine active environment
        self.active_env = self._get_active_environment()
        
        # Merged configuration (main + environment-specific)
        self.config = self._merge_configurations()

    def _load_properties_file(self, filename: str) -> Dict[str, Dict[str, str]]:
        """Load a .properties file into a nested dictionary.

        Args:
            filename: Name of the .properties file to load.

        Returns:
            A dictionary with sections as keys and key-value pairs as values.
        """
        config_path = self.config_dir / filename
        if not config_path.exists():
            return {}

        parser = configparser.ConfigParser()
        parser.read(config_path)
        
        # Convert to nested dictionary
        result = {}
        for section in parser.sections():
            result[section] = dict(parser[section])
        
        return result

    def _get_active_environment(self) -> str:
        """Get the active environment from configuration or environment variables.

        Returns:
            The active environment name (e.g., 'development', 'production').
        """
        # Check environment variable first
        env = os.environ.get("HAMILTON_ENVIRONMENT")
        
        # Fall back to config file
        if not env and 'environment' in self.env_config and 'active' in self.env_config['environment']:
            env = self.env_config['environment']['active']
        
        # Default to development
        return env or "development"

    def _merge_configurations(self) -> Dict[str, Dict[str, str]]:
        """Merge main and environment-specific configurations.

        Returns:
            A merged configuration dictionary.
        """
        result = {}
        
        # Start with main config
        for section, values in self.main_config.items():
            result[section] = values.copy()
        
        # Add environment-specific values
        for section, values in self.env_config.items():
            # Handle sections with environment suffix (e.g., database.development)
            section_parts = section.split('.')
            if len(section_parts) == 2 and section_parts[1] == self.active_env:
                # Add to base section (e.g., database)
                base_section = section_parts[0]
                if base_section not in result:
                    result[base_section] = {}
                result[base_section].update(values)
            elif len(section_parts) == 1:
                # Regular section
                if section not in result:
                    result[section] = {}
                result[section].update(values)
        
        return result

    def get(self, section: str, key: str, default: Any = None) -> Any:
        """Get a configuration value.

        Args:
            section: Configuration section.
            key: Configuration key.
            default: Default value if the key is not found.

        Returns:
            The configuration value or default if not found.
        """
        # Check environment variable first (e.g., HAMILTON_DATABASE_URL)
        env_var = f"HAMILTON_{section.upper()}_{key.upper()}"
        env_var = re.sub(r'[^A-Z0-9_]', '_', env_var)  # Replace invalid chars with underscore
        env_value = os.environ.get(env_var)
        if env_value is not None:
            return env_value
        
        # Check config
        if section in self.config and key in self.config[section]:
            return self.config[section][key]
        
        return default

    def get_int(self, section: str, key: str, default: Optional[int] = None) -> Optional[int]:
        """Get an integer configuration value.

        Args:
            section: Configuration section.
            key: Configuration key.
            default: Default value if the key is not found or not an integer.

        Returns:
            The integer value or default if not found or not an integer.
        """
        value = self.get(section, key, default)
        if value is None:
            return default
        
        try:
            return int(value)
        except (ValueError, TypeError):
            return default

    def get_float(self, section: str, key: str, default: Optional[float] = None) -> Optional[float]:
        """Get a float configuration value.

        Args:
            section: Configuration section.
            key: Configuration key.
            default: Default value if the key is not found or not a float.

        Returns:
            The float value or default if not found or not a float.
        """
        value = self.get(section, key, default)
        if value is None:
            return default
        
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    def get_bool(self, section: str, key: str, default: Optional[bool] = None) -> Optional[bool]:
        """Get a boolean configuration value.

        Args:
            section: Configuration section.
            key: Configuration key.
            default: Default value if the key is not found or not a boolean.

        Returns:
            The boolean value or default if not found or not a boolean.
        """
        value = self.get(section, key, default)
        if value is None:
            return default
        
        if isinstance(value, bool):
            return value
        
        if isinstance(value, str):
            value = value.lower()
            if value in ('true', 'yes', '1', 'on'):
                return True
            if value in ('false', 'no', '0', 'off'):
                return False
        
        return default

    def get_section(self, section: str) -> Dict[str, str]:
        """Get all key-value pairs in a section.

        Args:
            section: Configuration section.

        Returns:
            Dictionary of key-value pairs in the section or empty dict if not found.
        """
        return self.config.get(section, {}).copy()


# Singleton instance
_config_loader = None


def get_config() -> ConfigLoader:
    """Get the singleton ConfigLoader instance.

    Returns:
        The ConfigLoader instance.
    """
    global _config_loader
    if _config_loader is None:
        _config_loader = ConfigLoader()
    return _config_loader


# Example usage
if __name__ == "__main__":
    config = get_config()
    print(f"Active environment: {config.active_env}")
    print(f"Database URL: {config.get('database', 'db.url')}")
    print(f"Database username: {config.get('database', 'db.username')}")
    print(f"Log level: {config.get('application', 'app.log.level')}")
    print(f"Experimental features enabled: {config.get_bool('features', 'features.experimental.enabled')}")
