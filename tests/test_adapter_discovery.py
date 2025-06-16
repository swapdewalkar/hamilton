"""Tests for the adapter discovery system."""

import dataclasses
import os
import tempfile
from pathlib import Path
from typing import Any, Collection, Dict, Tuple, Type

import pytest

from hamilton.adapter_discovery import (
    AdapterDiscoveryError,
    AdapterRegistry,
    RuntimeAdapterLoader,
    discover_and_verify_adapters,
)
from hamilton.adapter_verification import AdapterVerifier
from hamilton.io.data_adapters import DataLoader, DataSaver


# Test adapter for file-based tests
TEST_ADAPTER_CODE = '''
"""Test adapters for discovery testing."""

import dataclasses
from typing import Any, Collection, Dict, Tuple, Type
from hamilton.io.data_adapters import DataLoader, DataSaver

@dataclasses.dataclass
class TestFileLoader(DataLoader):
    """Test loader from file."""
    
    param: str
    
    @classmethod
    def applicable_types(cls) -> Collection[Type]:
        return [str]
    
    @classmethod
    def name(cls) -> str:
        return "test_file_loader"
    
    def load_data(self, type_: Type) -> Tuple[Any, Dict[str, Any]]:
        return "test_data", {"param": self.param}


@dataclasses.dataclass
class TestFileSaver(DataSaver):
    """Test saver from file."""
    
    path: str
    
    @classmethod
    def applicable_types(cls) -> Collection[Type]:
        return [str]
    
    @classmethod
    def name(cls) -> str:
        return "test_file_saver"
    
    def save_data(self, data: Any) -> Dict[str, Any]:
        return {"saved": True}
'''


class TestRuntimeAdapterLoader:
    """Test the RuntimeAdapterLoader class."""
    
    def test_load_from_file_success(self):
        """Test successfully loading adapters from a file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test file
            test_file = Path(tmpdir) / "test_adapters.py"
            test_file.write_text(TEST_ADAPTER_CODE)
            
            loader = RuntimeAdapterLoader()
            adapters = loader.load_from_file(test_file)
            
            assert len(adapters) == 2
            adapter_names = {a.__name__ for a in adapters}
            assert 'TestFileLoader' in adapter_names
            assert 'TestFileSaver' in adapter_names
            
            # Check validation was performed
            results = loader.get_validation_results()
            assert len(results) == 2
            
            # Cleanup
            loader.cleanup()
    
    def test_load_from_file_not_found(self):
        """Test loading from non-existent file."""
        loader = RuntimeAdapterLoader()
        
        with pytest.raises(AdapterDiscoveryError, match="File not found"):
            loader.load_from_file("/non/existent/file.py")
    
    def test_load_from_file_not_python(self):
        """Test loading from non-Python file."""
        with tempfile.NamedTemporaryFile(suffix='.txt') as f:
            loader = RuntimeAdapterLoader()
            
            with pytest.raises(AdapterDiscoveryError, match="Not a Python file"):
                loader.load_from_file(f.name)
    
    def test_load_from_file_syntax_error(self):
        """Test loading file with syntax error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "bad_syntax.py"
            test_file.write_text("def bad syntax():")  # Invalid syntax
            
            loader = RuntimeAdapterLoader()
            
            with pytest.raises(AdapterDiscoveryError, match="Failed to load adapters"):
                loader.load_from_file(test_file)
    
    def test_load_from_directory(self):
        """Test loading adapters from a directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create multiple test files
            (Path(tmpdir) / "adapters1.py").write_text(TEST_ADAPTER_CODE)
            (Path(tmpdir) / "adapters2.py").write_text(TEST_ADAPTER_CODE)
            (Path(tmpdir) / "_private.py").write_text(TEST_ADAPTER_CODE)  # Should be skipped
            
            loader = RuntimeAdapterLoader()
            adapters = loader.load_from_directory(tmpdir)
            
            # Should load from 2 files (not _private.py)
            assert len(adapters) == 4  # 2 adapters per file
            
            loader.cleanup()
    
    def test_load_from_directory_recursive(self):
        """Test recursive directory loading."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create nested structure
            subdir = Path(tmpdir) / "subdir"
            subdir.mkdir()
            
            (Path(tmpdir) / "top.py").write_text(TEST_ADAPTER_CODE)
            (subdir / "nested.py").write_text(TEST_ADAPTER_CODE)
            
            loader = RuntimeAdapterLoader()
            adapters = loader.load_from_directory(tmpdir, recursive=True)
            
            assert len(adapters) == 4  # 2 files * 2 adapters each
            
            loader.cleanup()
    
    def test_load_from_directory_non_recursive(self):
        """Test non-recursive directory loading."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create nested structure
            subdir = Path(tmpdir) / "subdir"
            subdir.mkdir()
            
            (Path(tmpdir) / "top.py").write_text(TEST_ADAPTER_CODE)
            (subdir / "nested.py").write_text(TEST_ADAPTER_CODE)
            
            loader = RuntimeAdapterLoader()
            adapters = loader.load_from_directory(tmpdir, recursive=False)
            
            assert len(adapters) == 2  # Only from top.py
            
            loader.cleanup()
    
    def test_auto_verify_and_register(self):
        """Test automatic verification and registration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test_adapters.py"
            test_file.write_text(TEST_ADAPTER_CODE)
            
            loader = RuntimeAdapterLoader(auto_verify=True, auto_register=True)
            adapters = loader.load_from_file(test_file)
            
            # Check adapters were verified
            results = loader.get_validation_results()
            assert all(r.is_valid for r in results.values())
            
            # Check they were registered
            from hamilton.registry import LOADER_REGISTRY, SAVER_REGISTRY
            assert any('TestFileLoader' in str(type(a)) for a in LOADER_REGISTRY.get('test_file_loader', []))
            assert any('TestFileSaver' in str(type(a)) for a in SAVER_REGISTRY.get('test_file_saver', []))
            
            loader.cleanup()
    
    def test_get_valid_adapters(self):
        """Test getting only valid adapters."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create file with both valid and invalid adapters
            mixed_code = TEST_ADAPTER_CODE + '''

class InvalidAdapter(DataLoader):
    """Invalid adapter - missing methods."""
    pass
'''
            test_file = Path(tmpdir) / "mixed.py"
            test_file.write_text(mixed_code)
            
            loader = RuntimeAdapterLoader(auto_verify=True)
            all_adapters = loader.load_from_file(test_file)
            valid_adapters = loader.get_valid_adapters()
            
            assert len(all_adapters) == 3
            assert len(valid_adapters) == 2  # Only the valid ones
            
            loader.cleanup()
    
    def test_cleanup(self):
        """Test module cleanup."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "test_cleanup.py"
            test_file.write_text(TEST_ADAPTER_CODE)
            
            loader = RuntimeAdapterLoader()
            loader.load_from_file(test_file)
            
            # Check modules were loaded
            assert len(loader._loaded_modules) > 0
            module_names = list(loader._loaded_modules)
            
            # Cleanup
            loader.cleanup()
            
            # Check modules were removed
            assert len(loader._loaded_modules) == 0
            import sys
            for name in module_names:
                assert name not in sys.modules


class TestAdapterRegistry:
    """Test the AdapterRegistry class."""
    
    def test_discover_and_register_file(self):
        """Test discovering and registering from a file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "registry_test.py"
            test_file.write_text(TEST_ADAPTER_CODE)
            
            registry = AdapterRegistry()
            summary = registry.discover_and_register(test_file)
            
            assert summary['total_discovered'] == 2
            assert len(summary['data_loaders']) == 1
            assert len(summary['data_savers']) == 1
            assert 'TestFileLoader' in summary['data_loaders']
            assert 'TestFileSaver' in summary['data_savers']
    
    def test_discover_and_register_directory(self):
        """Test discovering and registering from a directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / "adapters1.py").write_text(TEST_ADAPTER_CODE)
            (Path(tmpdir) / "adapters2.py").write_text(TEST_ADAPTER_CODE)
            
            registry = AdapterRegistry()
            summary = registry.discover_and_register(tmpdir)
            
            assert summary['total_discovered'] == 4
            assert len(summary['data_loaders']) == 2
            assert len(summary['data_savers']) == 2
    
    def test_discover_and_register_multiple_sources(self):
        """Test discovering from multiple sources."""
        with tempfile.TemporaryDirectory() as tmpdir:
            file1 = Path(tmpdir) / "file1.py"
            file2 = Path(tmpdir) / "file2.py"
            file1.write_text(TEST_ADAPTER_CODE)
            file2.write_text(TEST_ADAPTER_CODE)
            
            registry = AdapterRegistry()
            summary = registry.discover_and_register([file1, file2])
            
            assert 'sources' in summary
            assert len(summary['sources']) == 2
            assert all(s['total_discovered'] == 2 for s in summary['sources'])
    
    def test_get_lifecycle_and_graph_adapters(self):
        """Test getting lifecycle and graph adapters."""
        # Create test code with lifecycle adapter
        lifecycle_code = '''
from hamilton.lifecycle.base import BasePreNodeExecute

class TestLifecycleAdapter(BasePreNodeExecute):
    def pre_node_execute(self, **kwargs):
        pass
'''
        
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "lifecycle.py"
            test_file.write_text(lifecycle_code)
            
            registry = AdapterRegistry()
            summary = registry.discover_and_register(test_file)
            
            assert len(summary['lifecycle_adapters']) == 1
            assert 'TestLifecycleAdapter' in summary['lifecycle_adapters']
            
            # Check it's stored
            lifecycle_adapters = registry.get_lifecycle_adapters()
            assert len(lifecycle_adapters) == 1


class TestConvenienceFunctions:
    """Test convenience functions."""
    
    def test_discover_and_verify_adapters(self):
        """Test the discover_and_verify_adapters function."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "convenience_test.py"
            test_file.write_text(TEST_ADAPTER_CODE)
            
            summary = discover_and_verify_adapters(test_file, strict=False)
            
            assert summary['total_discovered'] == 2
            assert all(
                summary['validation_results'][name]['valid'] 
                for name in summary['validation_results']
            )
    
    def test_discover_and_verify_adapters_strict(self):
        """Test strict mode verification."""
        # Create adapter with warnings
        warning_code = '''
from hamilton.io.data_adapters import DataLoader
from typing import Any, Collection, Dict, Tuple, Type

class WarningAdapter(DataLoader):
    @classmethod
    def applicable_types(cls) -> Collection[Type]:
        return []  # Empty - will generate warning
    
    @classmethod
    def name(cls) -> str:
        return "warning"
    
    def load_data(self, type_: Type) -> Tuple[Any, Dict[str, Any]]:
        return None, {}
'''
        
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = Path(tmpdir) / "warning_test.py"
            test_file.write_text(warning_code)
            
            # Non-strict mode - should be valid
            summary = discover_and_verify_adapters(test_file, strict=False)
            assert summary['validation_results']['WarningAdapter']['valid']
            
            # Strict mode - should be invalid
            summary_strict = discover_and_verify_adapters(test_file, strict=True)
            assert not summary_strict['validation_results']['WarningAdapter']['valid']
