"""Adapter verification utilities for validating adapters from dynamic/runtime-loaded modules.

This module provides comprehensive verification for Hamilton adapters including:
- Data adapters (DataLoader, DataSaver)
- Lifecycle adapters
- Graph adapters
- Runtime validation and discovery
"""

import importlib
import inspect
import logging
import sys
import types
from typing import Any, Dict, List, Optional, Set, Tuple, Type, Union

from hamilton.io.data_adapters import AdapterCommon, DataLoader, DataSaver
from hamilton.lifecycle.base import LifecycleAdapter
from hamilton.lifecycle.api import GraphAdapter
from hamilton.registry import LOADER_REGISTRY, SAVER_REGISTRY, register_adapter

logger = logging.getLogger(__name__)


class AdapterVerificationError(Exception):
    """Base exception for adapter verification errors."""
    pass


class AdapterValidationResult:
    """Result of adapter validation containing status and details."""
    
    def __init__(self, adapter_class: Type, is_valid: bool, errors: List[str] = None, 
                 warnings: List[str] = None, metadata: Dict[str, Any] = None):
        self.adapter_class = adapter_class
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []
        self.metadata = metadata or {}
    
    def __repr__(self):
        return (f"AdapterValidationResult(adapter={self.adapter_class.__name__}, "
                f"valid={self.is_valid}, errors={len(self.errors)}, warnings={len(self.warnings)})")


class AdapterVerifier:
    """Main class for verifying adapters from dynamic modules."""
    
    def __init__(self, strict_mode: bool = False):
        """Initialize the adapter verifier.
        
        Args:
            strict_mode: If True, warnings are treated as errors
        """
        self.strict_mode = strict_mode
        self._verified_adapters: Set[Type] = set()
    
    def verify_data_adapter(self, adapter_class: Type) -> AdapterValidationResult:
        """Verify a data adapter (DataLoader or DataSaver).
        
        Args:
            adapter_class: The adapter class to verify
            
        Returns:
            AdapterValidationResult with validation details
        """
        errors = []
        warnings = []
        metadata = {}
        
        # Check if it's a proper subclass
        if not issubclass(adapter_class, AdapterCommon):
            errors.append(f"{adapter_class.__name__} must inherit from AdapterCommon, DataLoader, or DataSaver")
            return AdapterValidationResult(adapter_class, False, errors)
        
        # Check required methods
        if issubclass(adapter_class, DataLoader):
            metadata['adapter_type'] = 'DataLoader'
            if not hasattr(adapter_class, 'load_data') or not callable(getattr(adapter_class, 'load_data')):
                errors.append("DataLoader must implement load_data() method")
        elif issubclass(adapter_class, DataSaver):
            metadata['adapter_type'] = 'DataSaver'
            if not hasattr(adapter_class, 'save_data') or not callable(getattr(adapter_class, 'save_data')):
                errors.append("DataSaver must implement save_data() method")
        else:
            warnings.append("Adapter inherits from AdapterCommon but not DataLoader or DataSaver")
            metadata['adapter_type'] = 'AdapterCommon'
        
        # Check applicable_types
        try:
            applicable_types = adapter_class.applicable_types()
            if not isinstance(applicable_types, (list, tuple, set)):
                errors.append("applicable_types() must return a collection of types")
            elif len(applicable_types) == 0:
                warnings.append("applicable_types() returns empty collection")
            metadata['applicable_types'] = list(applicable_types) if applicable_types else []
        except Exception as e:
            errors.append(f"Error calling applicable_types(): {str(e)}")
        
        # Check name method
        try:
            name = adapter_class.name()
            if not isinstance(name, str) or not name:
                errors.append("name() must return a non-empty string")
            metadata['name'] = name
        except Exception as e:
            errors.append(f"Error calling name(): {str(e)}")
        
        # Check required/optional arguments
        try:
            required_args = adapter_class.get_required_arguments()
            optional_args = adapter_class.get_optional_arguments()
            if not isinstance(required_args, dict) or not isinstance(optional_args, dict):
                errors.append("get_required_arguments() and get_optional_arguments() must return dicts")
            metadata['required_args'] = required_args
            metadata['optional_args'] = optional_args
        except Exception as e:
            warnings.append(f"Could not get argument specifications: {str(e)}")
        
        # Check if adapter is already registered
        if hasattr(adapter_class, 'name'):
            try:
                adapter_name = adapter_class.name()
                if adapter_class in LOADER_REGISTRY.get(adapter_name, []):
                    warnings.append(f"Adapter already registered in LOADER_REGISTRY as '{adapter_name}'")
                if adapter_class in SAVER_REGISTRY.get(adapter_name, []):
                    warnings.append(f"Adapter already registered in SAVER_REGISTRY as '{adapter_name}'")
            except:
                pass
        
        is_valid = len(errors) == 0 and (not self.strict_mode or len(warnings) == 0)
        return AdapterValidationResult(adapter_class, is_valid, errors, warnings, metadata)
    
    def verify_lifecycle_adapter(self, adapter_class: Type) -> AdapterValidationResult:
        """Verify a lifecycle adapter.
        
        Args:
            adapter_class: The adapter class to verify
            
        Returns:
            AdapterValidationResult with validation details
        """
        errors = []
        warnings = []
        metadata = {'adapter_type': 'LifecycleAdapter'}
        
        # Check if it's a proper lifecycle adapter
        if not issubclass(adapter_class, LifecycleAdapter):
            errors.append(f"{adapter_class.__name__} must inherit from a LifecycleAdapter base class")
            return AdapterValidationResult(adapter_class, False, errors)
        
        # Identify which lifecycle hooks are implemented
        implemented_hooks = []
        for attr_name in dir(adapter_class):
            if not attr_name.startswith('_'):
                attr = getattr(adapter_class, attr_name)
                if callable(attr) and hasattr(attr, '__name__'):
                    # Check if it's overridden from base class
                    for base in adapter_class.__mro__[1:]:
                        if hasattr(base, attr_name):
                            base_attr = getattr(base, attr_name)
                            if attr is not base_attr:
                                implemented_hooks.append(attr_name)
                                break
        
        if not implemented_hooks:
            warnings.append("No lifecycle hooks appear to be implemented")
        
        metadata['implemented_hooks'] = implemented_hooks
        
        is_valid = len(errors) == 0 and (not self.strict_mode or len(warnings) == 0)
        return AdapterValidationResult(adapter_class, is_valid, errors, warnings, metadata)
    
    def verify_graph_adapter(self, adapter_class: Type) -> AdapterValidationResult:
        """Verify a graph adapter.
        
        Args:
            adapter_class: The adapter class to verify
            
        Returns:
            AdapterValidationResult with validation details
        """
        errors = []
        warnings = []
        metadata = {'adapter_type': 'GraphAdapter'}
        
        # Check if it's a proper graph adapter
        if not issubclass(adapter_class, GraphAdapter):
            errors.append(f"{adapter_class.__name__} must inherit from GraphAdapter")
            return AdapterValidationResult(adapter_class, False, errors)
        
        # Check required abstract method
        if not hasattr(adapter_class, 'check_input_type'):
            errors.append("GraphAdapter must implement check_input_type() method")
        else:
            # Verify it's properly implemented (not abstract)
            try:
                # Check if method is still abstract
                if getattr(adapter_class.check_input_type, '__isabstractmethod__', False):
                    errors.append("check_input_type() method is still abstract")
            except:
                pass
        
        is_valid = len(errors) == 0 and (not self.strict_mode or len(warnings) == 0)
        return AdapterValidationResult(adapter_class, is_valid, errors, warnings, metadata)
    
    def verify_adapter(self, adapter_class: Type) -> AdapterValidationResult:
        """Verify any type of adapter automatically detecting its type.
        
        Args:
            adapter_class: The adapter class to verify
            
        Returns:
            AdapterValidationResult with validation details
        """
        # Check adapter type and delegate to appropriate verifier
        if issubclass(adapter_class, (DataLoader, DataSaver, AdapterCommon)):
            return self.verify_data_adapter(adapter_class)
        elif issubclass(adapter_class, GraphAdapter):
            return self.verify_graph_adapter(adapter_class)
        elif issubclass(adapter_class, LifecycleAdapter):
            return self.verify_lifecycle_adapter(adapter_class)
        else:
            return AdapterValidationResult(
                adapter_class, 
                False, 
                [f"{adapter_class.__name__} is not a recognized adapter type"]
            )
    
    def verify_and_register(self, adapter_class: Type, force: bool = False) -> AdapterValidationResult:
        """Verify an adapter and register it if valid.
        
        Args:
            adapter_class: The adapter class to verify and register
            force: If True, register even with warnings
            
        Returns:
            AdapterValidationResult with validation details
        """
        result = self.verify_adapter(adapter_class)
        
        if result.is_valid or (force and not result.errors):
            if issubclass(adapter_class, (DataLoader, DataSaver)):
                try:
                    register_adapter(adapter_class)
                    result.metadata['registered'] = True
                    logger.info(f"Successfully registered adapter: {adapter_class.__name__}")
                except Exception as e:
                    result.errors.append(f"Failed to register adapter: {str(e)}")
                    result.is_valid = False
            else:
                result.metadata['registered'] = False
                result.metadata['register_note'] = "Non-data adapters are not registered in the registry"
        
        return result


def discover_adapters_in_module(module: Union[str, types.ModuleType]) -> List[Type]:
    """Discover all adapter classes in a module.
    
    Args:
        module: Module name (string) or module object
        
    Returns:
        List of adapter classes found in the module
    """
    if isinstance(module, str):
        try:
            module = importlib.import_module(module)
        except ImportError as e:
            logger.error(f"Failed to import module {module}: {e}")
            return []
    
    adapters = []
    
    for name, obj in inspect.getmembers(module):
        if inspect.isclass(obj) and obj.__module__ == module.__name__:
            # Check if it's an adapter type
            if issubclass(obj, (AdapterCommon, LifecycleAdapter, GraphAdapter)):
                # Skip abstract base classes
                if not inspect.isabstract(obj):
                    adapters.append(obj)
    
    return adapters


def verify_module_adapters(module: Union[str, types.ModuleType], 
                          verifier: Optional[AdapterVerifier] = None,
                          auto_register: bool = False) -> Dict[Type, AdapterValidationResult]:
    """Verify all adapters in a module.
    
    Args:
        module: Module name (string) or module object
        verifier: AdapterVerifier instance (creates new one if None)
        auto_register: If True, automatically register valid data adapters
        
    Returns:
        Dictionary mapping adapter classes to their validation results
    """
    if verifier is None:
        verifier = AdapterVerifier()
    
    adapters = discover_adapters_in_module(module)
    results = {}
    
    for adapter_class in adapters:
        if auto_register:
            result = verifier.verify_and_register(adapter_class)
        else:
            result = verifier.verify_adapter(adapter_class)
        results[adapter_class] = result
        
        # Log results
        if result.is_valid:
            logger.info(f"✓ {adapter_class.__name__} is valid")
        else:
            logger.error(f"✗ {adapter_class.__name__} validation failed: {result.errors}")
        
        if result.warnings:
            for warning in result.warnings:
                logger.warning(f"  ⚠ {warning}")
    
    return results
