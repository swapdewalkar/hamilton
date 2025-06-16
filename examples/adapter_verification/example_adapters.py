"""Example adapters for demonstrating the adapter verification system."""

import dataclasses
import json
from typing import Any, Collection, Dict, Tuple, Type

from hamilton.io.data_adapters import DataLoader, DataSaver
from hamilton.lifecycle.base import BasePostNodeExecute, BasePreNodeExecute
from hamilton.lifecycle.api import GraphAdapter


# Example 1: Valid data loader
@dataclasses.dataclass
class CustomJSONLoader(DataLoader):
    """A valid custom JSON loader."""
    
    file_path: str
    encoding: str = "utf-8"
    
    @classmethod
    def applicable_types(cls) -> Collection[Type]:
        return [dict, list]
    
    @classmethod
    def name(cls) -> str:
        return "custom_json"
    
    def load_data(self, type_: Type) -> Tuple[Any, Dict[str, Any]]:
        with open(self.file_path, 'r', encoding=self.encoding) as f:
            data = json.load(f)
        
        metadata = {
            "file_path": self.file_path,
            "encoding": self.encoding,
            "size_bytes": len(json.dumps(data))
        }
        
        return data, metadata


# Example 2: Valid data saver
@dataclasses.dataclass
class CustomJSONSaver(DataSaver):
    """A valid custom JSON saver."""
    
    file_path: str
    indent: int = 2
    
    @classmethod
    def applicable_types(cls) -> Collection[Type]:
        return [dict, list]
    
    @classmethod
    def name(cls) -> str:
        return "custom_json"
    
    def save_data(self, data: Any) -> Dict[str, Any]:
        with open(self.file_path, 'w') as f:
            json.dump(data, f, indent=self.indent)
        
        return {
            "file_path": self.file_path,
            "indent": self.indent,
            "size_bytes": len(json.dumps(data))
        }


# Example 3: Invalid data loader (missing required method)
@dataclasses.dataclass
class BrokenLoader(DataLoader):
    """An invalid loader missing the load_data method."""
    
    file_path: str
    
    @classmethod
    def applicable_types(cls) -> Collection[Type]:
        return [str]
    
    @classmethod
    def name(cls) -> str:
        return "broken"
    
    # Missing load_data method!


# Example 4: Valid lifecycle adapter
class LoggingLifecycleAdapter(BasePreNodeExecute, BasePostNodeExecute):
    """A valid lifecycle adapter for logging."""
    
    def __init__(self, log_level: str = "INFO"):
        self.log_level = log_level
        self.execution_times = {}
    
    def pre_node_execute(self, node_name: str, **kwargs):
        """Log before node execution."""
        import time
        self.execution_times[node_name] = time.time()
        print(f"[{self.log_level}] Starting execution of node: {node_name}")
    
    def post_node_execute(self, node_name: str, result: Any, **kwargs):
        """Log after node execution."""
        import time
        elapsed = time.time() - self.execution_times.get(node_name, time.time())
        print(f"[{self.log_level}] Completed node: {node_name} in {elapsed:.3f}s")


# Example 5: Invalid adapter (wrong base class)
class NotAnAdapter:
    """This is not a valid adapter - doesn't inherit from any adapter base class."""
    
    def do_something(self):
        pass


# Example 6: Adapter with warnings
@dataclasses.dataclass
class WarningAdapter(DataLoader):
    """An adapter that will generate warnings during validation."""
    
    # No parameters - will generate warning about empty constructor
    
    @classmethod
    def applicable_types(cls) -> Collection[Type]:
        return []  # Empty types - will generate warning
    
    @classmethod
    def name(cls) -> str:
        return "warning_adapter"
    
    def load_data(self, type_: Type) -> Tuple[Any, Dict[str, Any]]:
        return None, {}


# Example 7: Custom graph adapter
class CustomGraphAdapter(GraphAdapter):
    """A custom graph adapter implementation."""
    
    @staticmethod
    def check_input_type(node_type: Type, input_value: Any) -> bool:
        """Custom type checking logic."""
        # Simple implementation - just check if value is instance of expected type
        try:
            return isinstance(input_value, node_type)
        except:
            return False
    
    def do_node_execute(self, node_name: str, **kwargs):
        """Custom node execution logic."""
        print(f"Executing node with custom adapter: {node_name}")
        return super().do_node_execute(node_name, **kwargs)
