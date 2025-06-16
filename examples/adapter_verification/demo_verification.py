"""Demonstration of the adapter verification system."""

import sys
from pathlib import Path

# Add hamilton to path if needed
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from hamilton.adapter_discovery import RuntimeAdapterLoader, discover_and_verify_adapters
from hamilton.adapter_verification import AdapterVerifier, verify_module_adapters

# Import the example adapters
import example_adapters


def demo_basic_verification():
    """Demonstrate basic adapter verification."""
    print("=" * 60)
    print("BASIC ADAPTER VERIFICATION DEMO")
    print("=" * 60)
    
    verifier = AdapterVerifier(strict_mode=False)
    
    # Test valid adapters
    print("\n1. Verifying CustomJSONLoader (should be valid):")
    result = verifier.verify_adapter(example_adapters.CustomJSONLoader)
    print(f"   Valid: {result.is_valid}")
    print(f"   Type: {result.metadata.get('adapter_type')}")
    print(f"   Applicable types: {result.metadata.get('applicable_types')}")
    
    print("\n2. Verifying CustomJSONSaver (should be valid):")
    result = verifier.verify_adapter(example_adapters.CustomJSONSaver)
    print(f"   Valid: {result.is_valid}")
    print(f"   Type: {result.metadata.get('adapter_type')}")
    
    print("\n3. Verifying BrokenLoader (should be invalid):")
    result = verifier.verify_adapter(example_adapters.BrokenLoader)
    print(f"   Valid: {result.is_valid}")
    print(f"   Errors: {result.errors}")
    
    print("\n4. Verifying LoggingLifecycleAdapter (should be valid):")
    result = verifier.verify_adapter(example_adapters.LoggingLifecycleAdapter)
    print(f"   Valid: {result.is_valid}")
    print(f"   Type: {result.metadata.get('adapter_type')}")
    print(f"   Implemented hooks: {result.metadata.get('implemented_hooks')}")
    
    print("\n5. Verifying NotAnAdapter (should be invalid):")
    result = verifier.verify_adapter(example_adapters.NotAnAdapter)
    print(f"   Valid: {result.is_valid}")
    print(f"   Errors: {result.errors}")
    
    print("\n6. Verifying WarningAdapter (should have warnings):")
    result = verifier.verify_adapter(example_adapters.WarningAdapter)
    print(f"   Valid: {result.is_valid}")
    print(f"   Warnings: {result.warnings}")


def demo_strict_mode():
    """Demonstrate strict mode verification."""
    print("\n" + "=" * 60)
    print("STRICT MODE VERIFICATION DEMO")
    print("=" * 60)
    
    # In strict mode, warnings are treated as errors
    strict_verifier = AdapterVerifier(strict_mode=True)
    
    print("\nVerifying WarningAdapter in strict mode:")
    result = strict_verifier.verify_adapter(example_adapters.WarningAdapter)
    print(f"   Valid: {result.is_valid} (warnings treated as errors)")
    print(f"   Warnings: {result.warnings}")


def demo_module_verification():
    """Demonstrate verifying all adapters in a module."""
    print("\n" + "=" * 60)
    print("MODULE VERIFICATION DEMO")
    print("=" * 60)
    
    print("\nVerifying all adapters in example_adapters module:")
    results = verify_module_adapters(example_adapters)
    
    print(f"\nFound {len(results)} adapter classes:")
    for adapter_class, result in results.items():
        status = "✓" if result.is_valid else "✗"
        print(f"  {status} {adapter_class.__name__}")
        if result.errors:
            for error in result.errors:
                print(f"      ERROR: {error}")
        if result.warnings:
            for warning in result.warnings:
                print(f"      WARNING: {warning}")


def demo_runtime_loading():
    """Demonstrate runtime adapter loading and verification."""
    print("\n" + "=" * 60)
    print("RUNTIME ADAPTER LOADING DEMO")
    print("=" * 60)
    
    loader = RuntimeAdapterLoader(auto_verify=True, auto_register=False)
    
    # Load from the example file
    example_file = Path(__file__).parent / "example_adapters.py"
    print(f"\nLoading adapters from: {example_file}")
    
    adapters = loader.load_from_file(example_file)
    print(f"Found {len(adapters)} adapter classes")
    
    # Get validation results
    validation_results = loader.get_validation_results()
    valid_adapters = loader.get_valid_adapters()
    
    print(f"\nValid adapters: {len(valid_adapters)}")
    for adapter in valid_adapters:
        print(f"  - {adapter.__name__}")
    
    invalid_count = len(validation_results) - len(valid_adapters)
    if invalid_count > 0:
        print(f"\nInvalid adapters: {invalid_count}")
        for adapter, result in validation_results.items():
            if not result.is_valid:
                print(f"  - {adapter.__name__}: {result.errors[0]}")


def demo_discovery_and_registration():
    """Demonstrate the high-level discovery and registration API."""
    print("\n" + "=" * 60)
    print("DISCOVERY AND REGISTRATION DEMO")
    print("=" * 60)
    
    # Discover and verify adapters from the current directory
    current_dir = Path(__file__).parent
    print(f"\nDiscovering adapters in: {current_dir}")
    
    summary = discover_and_verify_adapters(current_dir, strict=False)
    
    print("\nDiscovery Summary:")
    print(f"  Total discovered: {summary['total_discovered']}")
    print(f"  Data loaders: {len(summary['data_loaders'])}")
    print(f"  Data savers: {len(summary['data_savers'])}")
    print(f"  Lifecycle adapters: {len(summary['lifecycle_adapters'])}")
    print(f"  Graph adapters: {len(summary['graph_adapters'])}")
    
    if summary['data_loaders']:
        print(f"\n  Data Loaders: {', '.join(summary['data_loaders'])}")
    if summary['data_savers']:
        print(f"  Data Savers: {', '.join(summary['data_savers'])}")
    
    print("\n  Validation Results:")
    for adapter_name, result in summary['validation_results'].items():
        status = "✓" if result['valid'] else "✗"
        print(f"    {status} {adapter_name}")


def demo_verify_and_register():
    """Demonstrate verifying and registering adapters."""
    print("\n" + "=" * 60)
    print("VERIFY AND REGISTER DEMO")
    print("=" * 60)
    
    verifier = AdapterVerifier()
    
    print("\nVerifying and registering CustomJSONLoader:")
    result = verifier.verify_and_register(example_adapters.CustomJSONLoader)
    print(f"  Valid: {result.is_valid}")
    print(f"  Registered: {result.metadata.get('registered', False)}")
    
    # Check if it's in the registry
    from hamilton.registry import LOADER_REGISTRY
    if 'custom_json' in LOADER_REGISTRY:
        print(f"  Found in LOADER_REGISTRY: {example_adapters.CustomJSONLoader in LOADER_REGISTRY['custom_json']}")


if __name__ == "__main__":
    # Run all demos
    demo_basic_verification()
    demo_strict_mode()
    demo_module_verification()
    demo_runtime_loading()
    demo_discovery_and_registration()
    demo_verify_and_register()
    
    print("\n" + "=" * 60)
    print("DEMO COMPLETE")
    print("=" * 60)
