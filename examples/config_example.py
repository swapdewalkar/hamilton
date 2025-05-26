"""
Example script demonstrating how to use the Hamilton configuration system.

This script shows how to load and use environment-specific configuration
from the .properties files.
"""

import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from config.config_loader import get_config


def main():
    """Demonstrate configuration loading and usage."""
    # Get the configuration loader
    config = get_config()
    
    # Print the active environment
    print(f"Active environment: {config.active_env}")
    print("=" * 50)
    
    # Print database configuration
    print("Database Configuration:")
    print(f"  URL: {config.get('database', 'db.url')}")
    print(f"  Username: {config.get('database', 'db.username')}")
    print(f"  Password: {'*' * len(config.get('database', 'db.password'))}")
    print(f"  Pool Size: {config.get_int('database', 'db.pool.size')}")
    print(f"  Max Pool: {config.get_int('database', 'db.pool.max')}")
    print("=" * 50)
    
    # Print application configuration
    print("Application Configuration:")
    print(f"  Log Level: {config.get('application', 'app.log.level')}")
    print(f"  Log Path: {config.get('application', 'app.log.path')}")
    print(f"  Max Threads: {config.get_int('application', 'app.max.threads')}")
    print(f"  Data Directory: {config.get('application', 'app.data.dir')}")
    print("=" * 50)
    
    # Print feature flags
    print("Feature Flags:")
    print(f"  Experimental: {config.get_bool('features', 'features.experimental.enabled')}")
    print(f"  Telemetry: {config.get_bool('features', 'features.telemetry.enabled')}")
    print(f"  Power User Mode: {config.get_bool('features', 'features.power_user_mode')}")
    print(f"  Caching: {config.get_bool('features', 'features.caching.enabled')}")
    print("=" * 50)
    
    # Print timeout values
    print("Timeout Values:")
    print(f"  Default: {config.get_int('timeouts', 'timeout.default')} ms")
    print(f"  HTTP Connection: {config.get_int('timeouts', 'timeout.http.connection')} ms")
    print(f"  HTTP Read: {config.get_int('timeouts', 'timeout.http.read')} ms")
    print(f"  Cache Expiry: {config.get_int('timeouts', 'timeout.cache.expiry')} ms")
    print("=" * 50)
    
    # Print storage configuration
    print("Storage Configuration:")
    print(f"  Type: {config.get('storage', 'storage.type')}")
    print(f"  Local Path: {config.get('storage', 'storage.local.path')}")
    print(f"  S3 Bucket: {config.get('storage', 's3.bucket')}")
    print(f"  S3 Region: {config.get('storage', 's3.region')}")
    print("=" * 50)
    
    # Print API configuration
    print("API Configuration:")
    print(f"  Enabled: {config.get_bool('api', 'api.enabled')}")
    print(f"  Host: {config.get('api', 'api.host')}")
    print(f"  Port: {config.get_int('api', 'api.port')}")
    print(f"  Base Path: {config.get('api', 'api.base.path')}")
    print(f"  Rate Limit: {config.get_int('api', 'api.rate.limit')}")
    print("=" * 50)
    
    # Demonstrate environment variable override
    print("Environment Variable Override Example:")
    print(f"  Current Database URL: {config.get('database', 'db.url')}")
    
    # Set an environment variable to override the configuration
    os.environ["HAMILTON_DATABASE_DB_URL"] = "jdbc:postgresql://override.example.com:5432/hamilton_override"
    
    # Create a new config instance to pick up the environment variable
    new_config = get_config()
    print(f"  Overridden Database URL: {new_config.get('database', 'db.url')}")
    print("=" * 50)


if __name__ == "__main__":
    main()
