# Hamilton Configuration System

This directory contains configuration files and utilities for the Hamilton framework.

## Configuration Files

### hamilton.properties

The main configuration file containing default settings for the Hamilton framework. This file includes settings for:

- Database connections
- Application settings
- Feature flags
- Environment-specific settings
- Timeout values
- Storage configuration
- API configuration
- Authentication settings

### environment.properties

Environment-specific configuration that can be easily switched between different deployment environments (development, testing, staging, production). This file follows a section naming convention where sections are suffixed with the environment name:

```
[section.environment]
```

For example:
```
[database.development]
db.url=jdbc:postgresql://localhost:5432/hamilton_dev

[database.production]
db.url=jdbc:postgresql://db.production.example.com:5432/hamilton_production
```

The active environment is determined by:
1. The `HAMILTON_ENVIRONMENT` environment variable
2. The `active` setting in the `[environment]` section of `environment.properties`
3. Defaults to `development` if not specified

## Using the Configuration System

### Python API

The `config_loader.py` module provides a simple API for accessing configuration values:

```python
from config.config_loader import get_config

# Get the configuration loader
config = get_config()

# Get a string value
db_url = config.get('database', 'db.url')

# Get an integer value
pool_size = config.get_int('database', 'db.pool.size')

# Get a boolean value
experimental = config.get_bool('features', 'features.experimental.enabled')

# Get all values in a section
db_config = config.get_section('database')
```

### Environment Variable Overrides

Any configuration value can be overridden by setting an environment variable with the following naming convention:

```
HAMILTON_<SECTION>_<KEY>
```

For example, to override the database URL:

```bash
export HAMILTON_DATABASE_DB_URL=jdbc:postgresql://custom-db:5432/hamilton
```

Environment variables take precedence over values in the configuration files.

### Example Usage

See `examples/config_example.py` for a complete example of how to use the configuration system.

## Adding New Configuration

To add new configuration settings:

1. Add the default values to `hamilton.properties`
2. Add environment-specific values to `environment.properties`
3. Use the configuration in your code:

```python
from config.config_loader import get_config

config = get_config()
my_setting = config.get('my_section', 'my.setting')
```

## Best Practices

1. **Use environment-specific configuration** for values that change between environments
2. **Use environment variables** for sensitive information (passwords, API keys)
3. **Group related settings** in the same section
4. **Document all settings** with comments in the properties files
5. **Use appropriate types** (get_int, get_bool, get_float) when retrieving values
6. **Provide sensible defaults** for all settings
