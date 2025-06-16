import logging

from hamilton.io.default_data_loaders import DATA_ADAPTERS
from hamilton.registry import register_adapter

# Import adapter verification utilities
from hamilton.adapter_discovery import (  # noqa: F401
    AdapterRegistry,
    RuntimeAdapterLoader,
    adapter_registry,
    discover_and_verify_adapters,
)
from hamilton.adapter_verification import (  # noqa: F401
    AdapterValidationResult,
    AdapterVerifier,
    discover_adapters_in_module,
    verify_module_adapters,
)

logger = logging.getLogger(__name__)

registered = False
# Register all the default ones
if not registered:
    logger.debug(f"Registering default data loaders: {DATA_ADAPTERS}")
    for data_loader in DATA_ADAPTERS:
        register_adapter(data_loader)

registered = True
