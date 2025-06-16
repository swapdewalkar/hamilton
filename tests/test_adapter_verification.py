"""Tests for the adapter verification system."""

import dataclasses
import tempfile
from pathlib import Path
from typing import Any, Collection, Dict, Tuple, Type

import pytest

from hamilton.adapter_verification import (
    AdapterValidationResult,
    AdapterVerificationError,
    AdapterVerifier,
    discover_adapters_in_module,
    verify_module_adapters,
)
from hamilton.io.data_adapters import AdapterCommon, DataLoader, DataSaver
from hamilton.lifecycle.api import GraphAdapter
from hamilton.lifecycle.base import BasePostNodeExecute


# Test fixtures - various adapter implementations for testing

@dataclasses.dataclass
class ValidTestLoader(DataLoader):
    """A valid test data loader."""
    
    test_param: str
    
    @classmethod
    def applicable_types(cls) -> Collection[Type]:
        return [dict, str]
    
    @classmethod
    def name(cls) -> str:
        return "test_loader"
    
    def load_data(self, type_: Type) -> Tuple[Any, Dict[str, Any]]:
        return {"test": self.test_param}, {"source": "test"}


@dataclasses.dataclass
class ValidTestSaver(DataSaver):
    """A valid test data saver."""
    
    output_path: str
    
    @classmethod
    def applicable_types(cls) -> Collection[Type]:
        return [dict]
    
    @classmethod
    def name(cls) -> str:
        return "test_saver"
    
    def save_data(self, data: Any) -> Dict[str, Any]:
        return {"saved": True, "path": self.output_path}


class InvalidLoaderMissingMethod(DataLoader):
    """Invalid loader - missing load_data method."""
    
    @classmethod
    def applicable_types(cls) -> Collection[Type]:
        return [str]
    
    @classmethod
    def name(cls) -> str:
        return "invalid_loader"


class InvalidLoaderBadTypes(DataLoader):
    """Invalid loader - applicable_types returns wrong type."""
    
    @classmethod
    def applicable_types(cls) -> Collection[Type]:
        return "not a collection"  # Should return collection
    
    @classmethod
    def name(cls) -> str:
        return "bad_types_loader"
    
    def load_data(self, type_: Type) -> Tuple[Any, Dict[str, Any]]:
        return None, {}


class InvalidLoaderNoName(DataLoader):
    """Invalid loader - missing name method."""
    
    @classmethod
    def applicable_types(cls) -> Collection[Type]:
        return [str]
    
    def load_data(self, type_: Type) -> Tuple[Any, Dict[str, Any]]:
        return "", {}


class EmptyTypesLoader(DataLoader):
    """Loader with empty applicable types - should generate warning."""
    
    @classmethod
    def applicable_types(cls) -> Collection[Type]:
        return []
    
    @classmethod
    def name(cls) -> str:
        return "empty_types"
    
    def load_data(self, type_: Type) -> Tuple[Any, Dict[str, Any]]:
        return None, {}


class ValidLifecycleAdapter(BasePostNodeExecute):
    """A valid lifecycle adapter."""
    
    def post_node_execute(self, node_name: str, result: Any, **kwargs):
        print(f"Executed {node_name}")


class ValidGraphAdapter(GraphAdapter):
    """A valid graph adapter."""
    
    @staticmethod
    def check_input_type(node_type: Type, input_value: Any) -> bool:
        return True


class NotAnAdapter:
    """Not an adapter - doesn't inherit from any adapter base."""
    pass


# Tests for AdapterVerifier

class TestAdapterVerifier:
    """Test the AdapterVerifier class."""
    
    def test_verify_valid_data_loader(self):
        """Test verifying a valid data loader."""
        verifier = AdapterVerifier()
        result = verifier.verify_data_adapter(ValidTestLoader)
        
        assert result.is_valid
        assert len(result.errors) == 0
        assert result.metadata['adapter_type'] == 'DataLoader'
        assert result.metadata['name'] == 'test_loader'
        assert dict in result.metadata['applicable_types']
    
    def test_verify_valid_data_saver(self):
        """Test verifying a valid data saver."""
        verifier = AdapterVerifier()
        result = verifier.verify_data_adapter(ValidTestSaver)
        
        assert result.is_valid
        assert len(result.errors) == 0
        assert result.metadata['adapter_type'] == 'DataSaver'
        assert result.metadata['name'] == 'test_saver'
    
    def test_verify_invalid_loader_missing_method(self):
        """Test verifying a loader missing required method."""
        verifier = AdapterVerifier()
        result = verifier.verify_data_adapter(InvalidLoaderMissingMethod)
        
        assert not result.is_valid
        assert len(result.errors) > 0
        assert "load_data() method" in result.errors[0]
    
    def test_verify_invalid_loader_bad_types(self):
        """Test verifying a loader with invalid applicable_types."""
        verifier = AdapterVerifier()
        result = verifier.verify_data_adapter(InvalidLoaderBadTypes)
        
        assert not result.is_valid
        assert len(result.errors) > 0
        assert "applicable_types() must return a collection" in result.errors[0]
    
    def test_verify_invalid_loader_no_name(self):
        """Test verifying a loader without name method."""
        verifier = AdapterVerifier()
        result = verifier.verify_data_adapter(InvalidLoaderNoName)
        
        assert not result.is_valid
        assert len(result.errors) > 0
        assert "Error calling name()" in result.errors[0]
    
    def test_verify_empty_types_warning(self):
        """Test that empty applicable_types generates warning."""
        verifier = AdapterVerifier()
        result = verifier.verify_data_adapter(EmptyTypesLoader)
        
        assert result.is_valid  # Valid but with warning
        assert len(result.warnings) > 0
        assert "empty collection" in result.warnings[0]
    
    def test_verify_empty_types_strict_mode(self):
        """Test that warnings fail validation in strict mode."""
        verifier = AdapterVerifier(strict_mode=True)
        result = verifier.verify_data_adapter(EmptyTypesLoader)
        
        assert not result.is_valid  # Invalid in strict mode
        assert len(result.warnings) > 0
    
    def test_verify_lifecycle_adapter(self):
        """Test verifying a lifecycle adapter."""
        verifier = AdapterVerifier()
        result = verifier.verify_lifecycle_adapter(ValidLifecycleAdapter)
        
        assert result.is_valid
        assert result.metadata['adapter_type'] == 'LifecycleAdapter'
        assert 'post_node_execute' in result.metadata['implemented_hooks']
    
    def test_verify_graph_adapter(self):
        """Test verifying a graph adapter."""
        verifier = AdapterVerifier()
        result = verifier.verify_graph_adapter(ValidGraphAdapter)
        
        assert result.is_valid
        assert result.metadata['adapter_type'] == 'GraphAdapter'
    
    def test_verify_not_an_adapter(self):
        """Test verifying a non-adapter class."""
        verifier = AdapterVerifier()
        result = verifier.verify_adapter(NotAnAdapter)
        
        assert not result.is_valid
        assert "not a recognized adapter type" in result.errors[0]
    
    def test_verify_and_register(self):
        """Test verify and register functionality."""
        verifier = AdapterVerifier()
        
        # Create a unique adapter to avoid conflicts
        @dataclasses.dataclass
        class UniqueTestLoader(DataLoader):
            @classmethod
            def applicable_types(cls) -> Collection[Type]:
                return [str]
            
            @classmethod
            def name(cls) -> str:
                return "unique_test_loader_xyz"
            
            def load_data(self, type_: Type) -> Tuple[Any, Dict[str, Any]]:
                return "", {}
        
        result = verifier.verify_and_register(UniqueTestLoader)
        
        assert result.is_valid
        assert result.metadata.get('registered') is True
        
        # Check it's in the registry
        from hamilton.registry import LOADER_REGISTRY
        assert UniqueTestLoader in LOADER_REGISTRY.get('unique_test_loader_xyz', [])


class TestDiscoveryFunctions:
    """Test adapter discovery functions."""
    
    def test_discover_adapters_in_module(self):
        """Test discovering adapters in a module."""
        import tests.test_adapter_verification as test_module
        
        adapters = discover_adapters_in_module(test_module)
        
        # Should find our test adapters
        adapter_names = {adapter.__name__ for adapter in adapters}
        assert 'ValidTestLoader' in adapter_names
        assert 'ValidTestSaver' in adapter_names
        assert 'ValidLifecycleAdapter' in adapter_names
        assert 'ValidGraphAdapter' in adapter_names
        
        # Should not find non-adapters
        assert 'NotAnAdapter' not in adapter_names
    
    def test_verify_module_adapters(self):
        """Test verifying all adapters in a module."""
        import tests.test_adapter_verification as test_module
        
        results = verify_module_adapters(test_module)
        
        # Check we got results for all adapters
        assert ValidTestLoader in results
        assert ValidTestSaver in results
        assert InvalidLoaderMissingMethod in results
        
        # Check validity
        assert results[ValidTestLoader].is_valid
        assert results[ValidTestSaver].is_valid
        assert not results[InvalidLoaderMissingMethod].is_valid


class TestAdapterValidationResult:
    """Test the AdapterValidationResult class."""
    
    def test_validation_result_creation(self):
        """Test creating validation results."""
        result = AdapterValidationResult(
            adapter_class=ValidTestLoader,
            is_valid=True,
            errors=["error1"],
            warnings=["warning1"],
            metadata={"key": "value"}
        )
        
        assert result.adapter_class == ValidTestLoader
        assert result.is_valid
        assert result.errors == ["error1"]
        assert result.warnings == ["warning1"]
        assert result.metadata == {"key": "value"}
    
    def test_validation_result_repr(self):
        """Test string representation of validation result."""
        result = AdapterValidationResult(
            adapter_class=ValidTestLoader,
            is_valid=True,
            errors=["e1", "e2"],
            warnings=["w1"]
        )
        
        repr_str = repr(result)
        assert "ValidTestLoader" in repr_str
        assert "valid=True" in repr_str
        assert "errors=2" in repr_str
        assert "warnings=1" in repr_str
