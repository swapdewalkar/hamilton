# Hamilton Adapter Verification System

This directory contains examples demonstrating Hamilton's adapter verification system, which provides comprehensive validation and runtime discovery of adapters from dynamic or runtime-loaded modules.

## Overview

The adapter verification system helps ensure that adapters (data loaders/savers, lifecycle hooks, and graph adapters) are properly implemented and can be safely used in Hamilton workflows. It provides:

1. **Static Verification**: Validate adapter implementations against Hamilton's requirements
2. **Runtime Discovery**: Dynamically load and verify adapters from files, directories, or packages
3. **Automatic Registration**: Optionally register valid data adapters in Hamilton's registry
4. **Comprehensive Reporting**: Detailed validation results with errors, warnings, and metadata

## Key Components

### 1. AdapterVerifier

The main verification class that validates adapters:

```python
from hamilton.adapter_verification import AdapterVerifier

verifier = AdapterVerifier(strict_mode=False)  # strict_mode treats warnings as errors
result = verifier.verify_adapter(MyCustomAdapter)

if result.is_valid:
    print(f"✓ {MyCustomAdapter.__name__} is valid")
else:
    print(f"✗ Errors: {result.errors}")
```

### 2. RuntimeAdapterLoader

Loads adapters from various sources at runtime:

```python
from hamilton.adapter_discovery import RuntimeAdapterLoader

loader = RuntimeAdapterLoader(auto_verify=True, auto_register=False)

# Load from file
adapters = loader.load_from_file("path/to/adapters.py")

# Load from directory
adapters = loader.load_from_directory("path/to/adapter/dir", recursive=True)

# Load from package
adapters = loader.load_from_package("my.adapter.package")

# Get validation results
results = loader.get_validation_results()
valid_adapters = loader.get_valid_adapters()
```

### 3. High-Level Discovery API

Convenient functions for common use cases:

```python
from hamilton.adapter_discovery import discover_and_verify_adapters

# Discover and verify adapters from multiple sources
summary = discover_and_verify_adapters([
    "path/to/file.py",
    "path/to/directory",
    "my.package.name"
], strict=False)

print(f"Found {summary['total_discovered']} adapters")
print(f"Data loaders: {summary['data_loaders']}")
print(f"Data savers: {summary['data_savers']}")
```

## Validation Checks

### Data Adapters (DataLoader/DataSaver)

- ✓ Inherits from appropriate base class
- ✓ Implements required methods (`load_data` or `save_data`)
- ✓ `applicable_types()` returns a collection of types
- ✓ `name()` returns a non-empty string
- ✓ Required/optional arguments are properly defined
- ⚠ Warns if already registered
- ⚠ Warns if `applicable_types()` is empty

### Lifecycle Adapters

- ✓ Inherits from a lifecycle adapter base class
- ✓ Implements at least one lifecycle hook
- ⚠ Warns if no hooks are implemented

### Graph Adapters

- ✓ Inherits from GraphAdapter
- ✓ Implements `check_input_type()` method
- ✓ Method is not abstract

## Example Usage

### Basic Verification

```python
# example_adapters.py
import dataclasses
from typing import Any, Collection, Dict, Tuple, Type
from hamilton.io.data_adapters import DataLoader

@dataclasses.dataclass
class CustomJSONLoader(DataLoader):
    file_path: str
    
    @classmethod
    def applicable_types(cls) -> Collection[Type]:
        return [dict, list]
    
    @classmethod
    def name(cls) -> str:
        return "custom_json"
    
    def load_data(self, type_: Type) -> Tuple[Any, Dict[str, Any]]:
        import json
        with open(self.file_path, 'r') as f:
            data = json.load(f)
        return data, {"source": self.file_path}
```

### Verify and Use

```python
from hamilton.adapter_verification import AdapterVerifier
from hamilton.adapter_discovery import discover_and_verify_adapters

# Method 1: Direct verification
verifier = AdapterVerifier()
result = verifier.verify_and_register(CustomJSONLoader)

# Method 2: Discover from file
summary = discover_and_verify_adapters("example_adapters.py")

# Now use in Hamilton
from hamilton import driver
from hamilton.function_modifiers import load_from

@load_from.custom_json(file_path="data.json")
def my_data() -> dict:
    pass
```

### Runtime Discovery Example

```python
# Discover all adapters in a project
from hamilton.adapter_discovery import AdapterRegistry

registry = AdapterRegistry()

# Discover from multiple sources
summary = registry.discover_and_register([
    "src/adapters",           # Directory
    "custom_adapters.py",     # Single file
    "myproject.adapters"      # Package
])

# Use discovered adapters
loaders = registry.get_available_loaders()
savers = registry.get_available_savers()
lifecycle_adapters = registry.get_lifecycle_adapters()
```

## Running the Demo

To see the verification system in action:

```bash
cd examples/adapter_verification
python demo_verification.py
```

This will demonstrate:
- Basic adapter verification
- Strict mode validation
- Module-wide verification
- Runtime loading and discovery
- Automatic registration

## Best Practices

1. **Always Verify Before Use**: Verify adapters before using them in production
2. **Use Strict Mode in CI**: Enable strict mode in CI/CD to catch potential issues
3. **Document Adapter Requirements**: Clearly document required/optional parameters
4. **Handle Errors Gracefully**: Check validation results and handle invalid adapters
5. **Clean Up Dynamic Modules**: Call `loader.cleanup()` when done with runtime loading

## Common Issues and Solutions

### Issue: Adapter Not Found
**Solution**: Ensure the adapter class is properly imported and not abstract

### Issue: Registration Fails
**Solution**: Check that the adapter name is unique and methods are properly implemented

### Issue: Type Checking Fails
**Solution**: Ensure `applicable_types()` returns a proper collection of types

### Issue: Memory Leaks with Dynamic Loading
**Solution**: Always call `cleanup()` on RuntimeAdapterLoader when finished

## Integration with Hamilton

The verification system integrates seamlessly with Hamilton's existing adapter system:

```python
from hamilton import driver
from hamilton.adapter_discovery import discover_and_verify_adapters

# Discover and register adapters
discover_and_verify_adapters("my_adapters.py")

# Use in Hamilton driver
dr = driver.Builder().with_modules(...).build()

# Adapters are now available for use with decorators
# @load_from.my_custom_loader(...)
# @save_to.my_custom_saver(...)
```
