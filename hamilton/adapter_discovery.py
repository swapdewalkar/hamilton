"""Runtime adapter discovery and loading utilities.

This module provides functionality to discover and load adapters at runtime,
including from dynamically loaded modules, packages, and file paths.
"""

import importlib.util
import inspect
import logging
import os
import pkgutil
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Type, Union

from hamilton.adapter_verification import (
    AdapterValidationResult,
    AdapterVerifier,
    discover_adapters_in_module,
)
from hamilton.io.data_adapters import AdapterCommon, DataLoader, DataSaver
from hamilton.lifecycle.api import GraphAdapter
from hamilton.lifecycle.base import LifecycleAdapter
from hamilton.registry import LOADER_REGISTRY, SAVER_REGISTRY

logger = logging.getLogger(__name__)


class AdapterDiscoveryError(Exception):
    """Exception raised during adapter discovery."""
    pass


class RuntimeAdapterLoader:
    """Loads adapters from various sources at runtime."""
    
    def __init__(self, verifier: Optional[AdapterVerifier] = None, 
                 auto_verify: bool = True, auto_register: bool = False):
        """Initialize the runtime adapter loader.
        
        Args:
            verifier: AdapterVerifier instance for validation
            auto_verify: Automatically verify discovered adapters
            auto_register: Automatically register valid data adapters
        """
        self.verifier = verifier or AdapterVerifier()
        self.auto_verify = auto_verify
        self.auto_register = auto_register
        self._loaded_modules: Set[str] = set()
        self._discovered_adapters: Dict[Type, AdapterValidationResult] = {}
    
    def load_from_file(self, file_path: Union[str, Path]) -> List[Type]:
        """Load adapters from a Python file.
        
        Args:
            file_path: Path to the Python file
            
        Returns:
            List of adapter classes found in the file
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise AdapterDiscoveryError(f"File not found: {file_path}")
        
        if not file_path.suffix == '.py':
            raise AdapterDiscoveryError(f"Not a Python file: {file_path}")
        
        # Create a unique module name
        module_name = f"_dynamic_adapter_{file_path.stem}_{id(file_path)}"
        
        # Load the module dynamically
        spec = importlib.util.spec_from_file_location(module_name, file_path)
        if spec is None or spec.loader is None:
            raise AdapterDiscoveryError(f"Failed to load spec from {file_path}")
        
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        
        try:
            spec.loader.exec_module(module)
            self._loaded_modules.add(module_name)
            
            # Discover adapters in the module
            adapters = discover_adapters_in_module(module)
            
            # Verify if requested
            if self.auto_verify:
                for adapter in adapters:
                    result = self._verify_and_store(adapter)
                    if not result.is_valid:
                        logger.warning(f"Adapter {adapter.__name__} from {file_path} failed validation")
            
            return adapters
            
        except Exception as e:
            # Clean up on failure
            if module_name in sys.modules:
                del sys.modules[module_name]
            raise AdapterDiscoveryError(f"Failed to load adapters from {file_path}: {e}")
    
    def load_from_package(self, package_name: str, recursive: bool = True) -> List[Type]:
        """Load adapters from a package.
        
        Args:
            package_name: Name of the package to load
            recursive: Whether to search subpackages
            
        Returns:
            List of adapter classes found in the package
        """
        try:
            package = importlib.import_module(package_name)
        except ImportError as e:
            raise AdapterDiscoveryError(f"Failed to import package {package_name}: {e}")
        
        adapters = []
        
        # Get adapters from the main package module
        adapters.extend(discover_adapters_in_module(package))
        
        if recursive and hasattr(package, '__path__'):
            # Iterate through submodules
            for importer, modname, ispkg in pkgutil.walk_packages(
                package.__path__, prefix=package.__name__ + "."
            ):
                try:
                    module = importlib.import_module(modname)
                    module_adapters = discover_adapters_in_module(module)
                    adapters.extend(module_adapters)
                    
                    if self.auto_verify:
                        for adapter in module_adapters:
                            self._verify_and_store(adapter)
                            
                except Exception as e:
                    logger.warning(f"Failed to load module {modname}: {e}")
        
        return adapters
    
    def load_from_directory(self, directory: Union[str, Path], 
                           pattern: str = "*.py", recursive: bool = True) -> List[Type]:
        """Load adapters from all Python files in a directory.
        
        Args:
            directory: Directory path to search
            pattern: File pattern to match (default: "*.py")
            recursive: Whether to search subdirectories
            
        Returns:
            List of adapter classes found
        """
        directory = Path(directory)
        
        if not directory.exists():
            raise AdapterDiscoveryError(f"Directory not found: {directory}")
        
        if not directory.is_dir():
            raise AdapterDiscoveryError(f"Not a directory: {directory}")
        
        adapters = []
        
        # Find all matching files
        if recursive:
            files = directory.rglob(pattern)
        else:
            files = directory.glob(pattern)
        
        for file_path in files:
            if file_path.name.startswith('_'):
                continue  # Skip private modules
                
            try:
                file_adapters = self.load_from_file(file_path)
                adapters.extend(file_adapters)
            except Exception as e:
                logger.warning(f"Failed to load adapters from {file_path}: {e}")
        
        return adapters
    
    def _verify_and_store(self, adapter_class: Type) -> AdapterValidationResult:
        """Verify an adapter and store the result.
        
        Args:
            adapter_class: Adapter class to verify
            
        Returns:
            Validation result
        """
        if self.auto_register:
            result = self.verifier.verify_and_register(adapter_class)
        else:
            result = self.verifier.verify_adapter(adapter_class)
        
        self._discovered_adapters[adapter_class] = result
        return result
    
    def get_validation_results(self) -> Dict[Type, AdapterValidationResult]:
        """Get all validation results for discovered adapters.
        
        Returns:
            Dictionary mapping adapter classes to validation results
        """
        return self._discovered_adapters.copy()
    
    def get_valid_adapters(self) -> List[Type]:
        """Get all valid adapters that were discovered.
        
        Returns:
            List of valid adapter classes
        """
        return [
            adapter for adapter, result in self._discovered_adapters.items()
            if result.is_valid
        ]
    
    def cleanup(self):
        """Clean up dynamically loaded modules."""
        for module_name in self._loaded_modules:
            if module_name in sys.modules:
                del sys.modules[module_name]
        self._loaded_modules.clear()


class AdapterRegistry:
    """Enhanced adapter registry with runtime discovery capabilities."""
    
    def __init__(self):
        self._custom_loaders: Dict[str, List[Type[DataLoader]]] = {}
        self._custom_savers: Dict[str, List[Type[DataSaver]]] = {}
        self._lifecycle_adapters: List[Type[LifecycleAdapter]] = []
        self._graph_adapters: List[Type[GraphAdapter]] = []
    
    def discover_and_register(self, source: Union[str, Path, List[Union[str, Path]]], 
                            verifier: Optional[AdapterVerifier] = None) -> Dict[str, Any]:
        """Discover and register adapters from various sources.
        
        Args:
            source: File path, directory, package name, or list of sources
            verifier: Optional verifier for validation
            
        Returns:
            Summary of discovered and registered adapters
        """
        if isinstance(source, list):
            results = []
            for s in source:
                results.append(self.discover_and_register(s, verifier))
            return {"sources": results}
        
        loader = RuntimeAdapterLoader(verifier=verifier, auto_verify=True, auto_register=True)
        
        source_path = Path(source) if not isinstance(source, Path) else source
        
        try:
            if source_path.exists():
                if source_path.is_file():
                    adapters = loader.load_from_file(source_path)
                else:
                    adapters = loader.load_from_directory(source_path)
            else:
                # Assume it's a package name
                adapters = loader.load_from_package(str(source))
            
            # Categorize adapters
            summary = {
                "source": str(source),
                "total_discovered": len(adapters),
                "data_loaders": [],
                "data_savers": [],
                "lifecycle_adapters": [],
                "graph_adapters": [],
                "validation_results": {}
            }
            
            validation_results = loader.get_validation_results()
            
            for adapter in adapters:
                result = validation_results.get(adapter)
                if result and result.is_valid:
                    if issubclass(adapter, DataLoader):
                        summary["data_loaders"].append(adapter.__name__)
                    elif issubclass(adapter, DataSaver):
                        summary["data_savers"].append(adapter.__name__)
                    elif issubclass(adapter, LifecycleAdapter):
                        summary["lifecycle_adapters"].append(adapter.__name__)
                        self._lifecycle_adapters.append(adapter)
                    elif issubclass(adapter, GraphAdapter):
                        summary["graph_adapters"].append(adapter.__name__)
                        self._graph_adapters.append(adapter)
                
                if result:
                    summary["validation_results"][adapter.__name__] = {
                        "valid": result.is_valid,
                        "errors": result.errors,
                        "warnings": result.warnings
                    }
            
            return summary
            
        finally:
            loader.cleanup()
    
    def get_available_loaders(self) -> Dict[str, List[Type[DataLoader]]]:
        """Get all available data loaders including custom ones.
        
        Returns:
            Dictionary mapping loader names to loader classes
        """
        all_loaders = dict(LOADER_REGISTRY)
        all_loaders.update(self._custom_loaders)
        return all_loaders
    
    def get_available_savers(self) -> Dict[str, List[Type[DataSaver]]]:
        """Get all available data savers including custom ones.
        
        Returns:
            Dictionary mapping saver names to saver classes
        """
        all_savers = dict(SAVER_REGISTRY)
        all_savers.update(self._custom_savers)
        return all_savers
    
    def get_lifecycle_adapters(self) -> List[Type[LifecycleAdapter]]:
        """Get discovered lifecycle adapters.
        
        Returns:
            List of lifecycle adapter classes
        """
        return self._lifecycle_adapters.copy()
    
    def get_graph_adapters(self) -> List[Type[GraphAdapter]]:
        """Get discovered graph adapters.
        
        Returns:
            List of graph adapter classes
        """
        return self._graph_adapters.copy()


# Global registry instance
adapter_registry = AdapterRegistry()


def discover_and_verify_adapters(sources: Union[str, Path, List[Union[str, Path]]], 
                               strict: bool = False) -> Dict[str, Any]:
    """Convenience function to discover and verify adapters from sources.
    
    Args:
        sources: File paths, directories, or package names to search
        strict: Whether to use strict verification mode
        
    Returns:
        Summary of discovered adapters and their validation status
    """
    verifier = AdapterVerifier(strict_mode=strict)
    return adapter_registry.discover_and_register(sources, verifier)
