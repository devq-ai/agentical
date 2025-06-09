"""
Test Helper Functions for Agentical

This module provides utility functions and decorators to simplify test
implementation and improve test reliability.
"""

import os
import json
import asyncio
import functools
import contextlib
import tempfile
from typing import Dict, Any, List, Optional, Union, Callable, Type, TypeVar, cast
from pathlib import Path

import pytest
from fastapi import FastAPI

# Type variable for function return types
T = TypeVar('T')


def async_test(f):
    """
    Decorator to run async test functions.
    
    This decorator allows you to use async functions in pytest without
    requiring the pytest-asyncio plugin explicitly in each test.
    
    Args:
        f: The async test function to wrap
        
    Returns:
        A wrapped test function that can be called by pytest
    """
    @functools.wraps(f)
    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(f(*args, **kwargs))
    return wrapper


def load_test_data(filename: str, base_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load test data from a JSON file.
    
    Args:
        filename: Name of the JSON file to load
        base_path: Base directory path (defaults to tests/fixtures)
        
    Returns:
        Loaded data as a dictionary
        
    Raises:
        FileNotFoundError: If the file doesn't exist
    """
    if base_path is None:
        # Get the path to the tests directory
        current_file = Path(__file__)
        tests_dir = current_file.parent.parent
        base_path = str(tests_dir / 'fixtures')
    
    # Ensure .json extension
    if not filename.endswith('.json'):
        filename += '.json'
    
    # Load the file
    file_path = os.path.join(base_path, filename)
    with open(file_path, 'r') as f:
        return json.load(f)


async def wait_for_completion(
    check_func: Callable[[], Union[bool, Any]], 
    timeout: float = 5.0,
    interval: float = 0.1
) -> bool:
    """
    Wait for an operation to complete within a timeout period.
    
    Args:
        check_func: Function that returns True/truthy when the operation is complete
        timeout: Maximum time to wait in seconds
        interval: Check interval in seconds
        
    Returns:
        True if the operation completed within the timeout, False otherwise
    """
    end_time = asyncio.get_event_loop().time() + timeout
    
    while asyncio.get_event_loop().time() < end_time:
        if check_func():
            return True
        await asyncio.sleep(interval)
    
    return False


def compare_json_objects(actual: Dict[str, Any], expected: Dict[str, Any], 
                        ignore_keys: Optional[List[str]] = None) -> Tuple[bool, List[str]]:
    """
    Compare two JSON objects for equality, ignoring specified keys.
    
    Args:
        actual: The actual JSON object
        expected: The expected JSON object
        ignore_keys: List of keys to ignore in the comparison
        
    Returns:
        Tuple of (is_equal, differences), where differences is a list of
        string descriptions of the differences found
    """
    ignore_keys = ignore_keys or []
    differences = []
    
    # Helper function to recursively compare objects
    def _compare(path, actual_val, expected_val):
        # Skip ignored keys
        if path in ignore_keys:
            return
        
        # Different types
        if type(actual_val) != type(expected_val):
            differences.append(f"{path}: Type mismatch - expected {type(expected_val).__name__}, got {type(actual_val).__name__}")
            return
        
        # Handle dictionaries
        if isinstance(actual_val, dict):
            # Check for missing or extra keys
            actual_keys = set(actual_val.keys())
            expected_keys = set(expected_val.keys())
            
            # Extra keys
            for key in actual_keys - expected_keys:
                if f"{path}.{key}" not in ignore_keys:
                    differences.append(f"{path}.{key}: Extra key in actual")
            
            # Missing keys
            for key in expected_keys - actual_keys:
                if f"{path}.{key}" not in ignore_keys:
                    differences.append(f"{path}.{key}: Missing key in actual")
            
            # Recursively compare values for common keys
            for key in actual_keys & expected_keys:
                _compare(f"{path}.{key}" if path else key, 
                         actual_val[key], expected_val[key])
        
        # Handle lists
        elif isinstance(actual_val, list):
            if len(actual_val) != len(expected_val):
                differences.append(f"{path}: List length mismatch - expected {len(expected_val)}, got {len(actual_val)}")
                return
            
            # For simple lists, compare items directly
            if all(not isinstance(x, (dict, list)) for x in actual_val + expected_val):
                if set(actual_val) != set(expected_val):
                    differences.append(f"{path}: List contents differ")
            else:
                # For complex lists, compare items by position
                for i, (a_item, e_item) in enumerate(zip(actual_val, expected_val)):
                    _compare(f"{path}[{i}]", a_item, e_item)
        
        # Compare other values directly
        elif actual_val != expected_val:
            differences.append(f"{path}: Value mismatch - expected {expected_val}, got {actual_val}")
    
    # Start comparison at root
    _compare("", actual, expected)
    
    return len(differences) == 0, differences


@contextlib.contextmanager
def isolate_test_execution():
    """
    Context manager to isolate test execution.
    
    This ensures that each test has a clean environment by:
    1. Creating a temporary directory for file operations
    2. Setting up environment isolation
    3. Cleaning up after the test
    
    Yields:
        Path to the temporary directory
    """
    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Store original environment
        original_env = os.environ.copy()
        
        try:
            # Set up test environment
            os.environ["TESTING"] = "1"
            os.environ["TEST_TEMP_DIR"] = temp_dir
            
            # Yield the temporary directory path
            yield Path(temp_dir)
            
        finally:
            # Restore original environment
            os.environ.clear()
            os.environ.update(original_env)


def create_test_app() -> FastAPI:
    """
    Create a FastAPI application for testing.
    
    This creates a minimal FastAPI app that can be used for testing
    API endpoints and middleware.
    
    Returns:
        FastAPI application instance
    """
    from fastapi import FastAPI, Depends, HTTPException, status
    from pydantic import BaseModel
    
    app = FastAPI(title="Test App", description="FastAPI app for testing")
    
    class Item(BaseModel):
        id: Optional[int] = None
        name: str
        description: Optional[str] = None
    
    items = {}
    
    @app.get("/items", response_model=List[Item])
    async def get_items():
        return list(items.values())
    
    @app.get("/items/{item_id}", response_model=Item)
    async def get_item(item_id: int):
        if item_id not in items:
            raise HTTPException(status_code=404, detail="Item not found")
        return items[item_id]
    
    @app.post("/items", response_model=Item, status_code=status.HTTP_201_CREATED)
    async def create_item(item: Item):
        item_id = max(items.keys(), default=0) + 1
        item.id = item_id
        items[item_id] = item
        return item
    
    @app.put("/items/{item_id}", response_model=Item)
    async def update_item(item_id: int, item: Item):
        if item_id not in items:
            raise HTTPException(status_code=404, detail="Item not found")
        item.id = item_id
        items[item_id] = item
        return item
    
    @app.delete("/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
    async def delete_item(item_id: int):
        if item_id not in items:
            raise HTTPException(status_code=404, detail="Item not found")
        del items[item_id]
        
    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}
    
    return app