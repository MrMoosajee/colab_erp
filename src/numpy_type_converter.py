"""
NumPy Type Converter - Converts numpy types to Python native types for database compatibility.

This module provides functions to safely convert numpy types (like numpy.int64, numpy.float64, etc.)
to Python native types that psycopg2 can adapt to PostgreSQL types.

Usage:
    from src.numpy_type_converter import convert_to_native, convert_params_to_native
    
    # Convert a single value
    native_value = convert_to_native(numpy_int64_value)
    
    # Convert all parameters in a tuple/list
    clean_params = convert_params_to_native(params_tuple)
"""

import numpy as np
import pandas as pd
from datetime import datetime, date, time
from decimal import Decimal
from typing import Any, Union, List, Tuple, Dict, Optional

# Mapping of numpy types to Python native types
# Note: np.unicode_ was removed in NumPy 2.0, np.str_ is used instead
NUMPY_TYPE_MAP = {
    np.int8: int,
    np.int16: int,
    np.int32: int,
    np.int64: int,
    np.uint8: int,
    np.uint16: int,
    np.uint32: int,
    np.uint64: int,
    np.float16: float,
    np.float32: float,
    np.float64: float,
}

# Add float128 if available (platform-dependent)
try:
    NUMPY_TYPE_MAP[np.float128] = float
except AttributeError:
    pass  # float128 not available on this platform


def is_numpy_type(value: Any) -> bool:
    """
    Check if a value is a numpy type (not a standard Python type).
    
    Args:
        value: Any value to check
        
    Returns:
        True if the value is a numpy type, False otherwise
    """
    if value is None:
        return False
    
    # Check if it's a numpy scalar type
    if isinstance(value, np.generic):
        return True
    
    # Check if it's a numpy array (any size - arrays contain numpy types)
    if isinstance(value, np.ndarray):
        return True
    
    return False


def convert_to_native(value: Any) -> Any:
    """
    Convert a numpy type to its Python native equivalent.
    
    Handles:
    - numpy.int64 -> int
    - numpy.float64 -> float
    - numpy.bool_ -> bool
    - numpy.str_ -> str
    - numpy.datetime64 -> datetime or date
    - pandas.Timestamp -> datetime
    - numpy arrays with single elements -> native type
    - numpy arrays with multiple elements -> list
    - Lists/tuples/dicts containing numpy types (recursively)
    - None values pass through unchanged
    
    Args:
        value: Any value, potentially a numpy type
        
    Returns:
        The value converted to a Python native type
    """
    if value is None:
        return None
    
    # Handle numpy arrays with single elements
    if isinstance(value, np.ndarray):
        if value.size == 1:
            return convert_to_native(value.item())
        else:
            # Convert array elements recursively
            return [convert_to_native(item) for item in value.tolist()]
    
    # Handle pandas Timestamp
    if isinstance(value, pd.Timestamp):
        return value.to_pydatetime()
    
    # Handle numpy datetime64 - return datetime or date depending on precision
    if isinstance(value, np.datetime64):
        ts = pd.Timestamp(value)
        # If no time component, return date, otherwise return datetime
        if ts.hour == 0 and ts.minute == 0 and ts.second == 0 and ts.microsecond == 0:
            return ts.date()
        return ts.to_pydatetime()
    
    # Handle pandas Series with single element
    if isinstance(value, pd.Series):
        if len(value) == 1:
            return convert_to_native(value.iloc[0])
        else:
            return [convert_to_native(item) for item in value.tolist()]
    
    # Handle pandas DataFrame (shouldn't happen but just in case)
    if isinstance(value, pd.DataFrame):
        return value.to_dict('records')
    
    # Handle numpy scalar types
    if isinstance(value, np.generic):
        # Use numpy's item() method for scalars
        return value.item()
    
    # Recursively handle lists
    if isinstance(value, list):
        return [convert_to_native(item) for item in value]
    
    # Recursively handle tuples
    if isinstance(value, tuple):
        return tuple(convert_to_native(item) for item in value)
    
    # Recursively handle dicts
    if isinstance(value, dict):
        return {key: convert_to_native(val) for key, val in value.items()}
    
    # Already a native type, return as-is
    return value


def convert_params_to_native(params: Optional[Union[Tuple, List, Dict]]) -> Optional[Union[Tuple, List, Dict]]:
    """
    Convert all numpy types in a parameters collection to native Python types.
    
    This is the main entry point for database operations. It handles:
    - Tuple parameters (most common for psycopg2)
    - List parameters
    - Dict parameters (for named placeholders)
    - None returns None
    
    Args:
        params: A tuple, list, or dict containing parameters, potentially with numpy types
        
    Returns:
        Parameters with all numpy types converted to native types
        
    Example:
        >>> params = (np.int64(42), np.float64(3.14), 'string')
        >>> clean_params = convert_params_to_native(params)
        >>> print(clean_params)  # (42, 3.14, 'string')
    """
    if params is None:
        return None
    
    if isinstance(params, dict):
        return {key: convert_to_native(value) for key, value in params.items()}
    
    if isinstance(params, (list, tuple)):
        converted = tuple(convert_to_native(item) for item in params)
        # Return same type as input
        return converted if isinstance(params, tuple) else list(converted)
    
    # Single value
    return convert_to_native(params)


def deep_convert(obj: Any) -> Any:
    """
    Deep convert numpy types in nested data structures.
    
    This handles complex nested structures like lists of dicts, dicts containing lists, etc.
    
    Args:
        obj: Any Python object that might contain numpy types
        
    Returns:
        The object with all numpy types converted to native types
        
    Example:
        >>> data = {
        ...     'id': np.int64(123),
        ...     'items': [np.float64(1.5), np.float64(2.5)],
        ...     'nested': {'count': np.int32(10)}
        ... }
        >>> clean_data = deep_convert(data)
    """
    if obj is None:
        return None
    
    if isinstance(obj, np.generic):
        return obj.item()
    
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    
    if isinstance(obj, pd.Timestamp):
        return obj.to_pydatetime()
    
    if isinstance(obj, np.datetime64):
        ts = pd.Timestamp(obj)
        if ts.hour == 0 and ts.minute == 0 and ts.second == 0 and ts.microsecond == 0:
            return ts.date()
        return ts.to_pydatetime()
    
    if isinstance(obj, (list, tuple)):
        converted = tuple(deep_convert(item) for item in obj)
        return converted if isinstance(obj, tuple) else list(converted)
    
    if isinstance(obj, dict):
        return {deep_convert(k): deep_convert(v) for k, v in obj.items()}
    
    return obj


# Convenience function for database operations
def prepare_for_db(params: Any) -> Any:
    """
    Alias for convert_params_to_native for use in database layer.
    
    This is a convenience function with a descriptive name for clarity
    in database code.
    
    Args:
        params: Parameters to convert for database use
        
    Returns:
        Parameters safe for database insertion
    """
    return convert_params_to_native(params)


# Validation function for testing
def validate_native_types(params: Any) -> Tuple[bool, Optional[str]]:
    """
    Validate that a parameter collection contains no numpy types.
    
    Args:
        params: Parameters to validate
        
    Returns:
        Tuple of (is_valid, error_message)
        is_valid is True if no numpy types found, False otherwise
        error_message describes any numpy types found
    """
    if params is None:
        return True, None
    
    numpy_items = []
    
    def check_item(item: Any, path: str = ""):
        if item is None:
            return
        
        if isinstance(item, (np.generic, np.ndarray)):
            numpy_items.append(f"{path}: {type(item).__name__}")
            return
        
        if isinstance(item, (pd.Timestamp, pd.Series, pd.DataFrame)):
            numpy_items.append(f"{path}: {type(item).__name__}")
            return
        
        if isinstance(item, (list, tuple)):
            for i, sub_item in enumerate(item):
                check_item(sub_item, f"{path}[{i}]")
        
        if isinstance(item, dict):
            for key, val in item.items():
                check_item(val, f"{path}[{key}]")
    
    check_item(params, "params")
    
    if numpy_items:
        return False, f"Found numpy types: {', '.join(numpy_items)}"
    
    return True, None


# Optional: Register with psycopg2 if needed (advanced usage)
def register_numpy_adapter():
    """
    Register a custom adapter with psycopg2 to handle numpy types automatically.
    
    This is an alternative approach that registers adapters at the psycopg2 level.
    Use this if you want global automatic conversion without modifying db.py calls.
    
    Note: This modifies global psycopg2 state and should be called once at startup.
    """
    import psycopg2
    
    def adapt_numpy_int(val):
        return psycopg2.extensions.Int(int(val))
    
    def adapt_numpy_float(val):
        return psycopg2.extensions.Float(float(val))
    
    def adapt_numpy_bool(val):
        return psycopg2.extensions.Boolean(bool(val))
    
    # Register adapters for common numpy types
    psycopg2.extensions.register_adapter(np.int8, adapt_numpy_int)
    psycopg2.extensions.register_adapter(np.int16, adapt_numpy_int)
    psycopg2.extensions.register_adapter(np.int32, adapt_numpy_int)
    psycopg2.extensions.register_adapter(np.int64, adapt_numpy_int)
    psycopg2.extensions.register_adapter(np.uint8, adapt_numpy_int)
    psycopg2.extensions.register_adapter(np.uint16, adapt_numpy_int)
    psycopg2.extensions.register_adapter(np.uint32, adapt_numpy_int)
    psycopg2.extensions.register_adapter(np.uint64, adapt_numpy_int)
    psycopg2.extensions.register_adapter(np.float16, adapt_numpy_float)
    psycopg2.extensions.register_adapter(np.float32, adapt_numpy_float)
    psycopg2.extensions.register_adapter(np.float64, adapt_numpy_float)
    psycopg2.extensions.register_adapter(np.bool_, adapt_numpy_bool)


if __name__ == "__main__":
    # Simple self-test
    print("Testing numpy_type_converter...")
    
    # Test single conversions
    test_cases = [
        (np.int64(42), int, 42),
        (np.float64(3.14), float, 3.14),
        (np.bool_(True), bool, True),
        (np.str_("test"), str, "test"),
        (pd.Timestamp("2024-01-01"), datetime, datetime(2024, 1, 1)),
        (None, type(None), None),
        (42, int, 42),  # Already native
        ("string", str, "string"),  # Already native
    ]
    
    for value, expected_type, expected_value in test_cases:
        result = convert_to_native(value)
        assert isinstance(result, expected_type), f"Expected {expected_type}, got {type(result)}"
        assert result == expected_value, f"Expected {expected_value}, got {result}"
        print(f"✓ convert_to_native({type(value).__name__}) = {result}")
    
    # Test tuple conversion
    params = (np.int64(42), np.float64(3.14), "string", None, np.bool_(True))
    clean_params = convert_params_to_native(params)
    assert clean_params == (42, 3.14, "string", None, True)
    print(f"✓ convert_params_to_native(tuple) = {clean_params}")
    
    # Test validation
    is_valid, error = validate_native_types(params)
    assert not is_valid, "Should find numpy types"
    print(f"✓ validate_native_types correctly detected numpy types")
    
    is_valid, error = validate_native_types(clean_params)
    assert is_valid, "Should not find numpy types after conversion"
    print(f"✓ validate_native_types confirmed clean params")
    
    print("\nAll tests passed! ✓")
