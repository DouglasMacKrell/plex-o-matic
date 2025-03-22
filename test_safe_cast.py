#!/usr/bin/env python3
"""Standalone test for safe_cast module."""

import sys
import os
from pathlib import Path

# Add the root directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from plexomatic.utils.safe_cast import safe_cast, safe_int, safe_float, safe_bool

def test_safe_cast():
    """Test safe_cast function."""
    # Test basic casting
    assert safe_cast("123", int) == 123
    assert safe_cast("3.14", float) == 3.14
    assert safe_cast("true", str) == "true"
    
    # Test failure cases
    assert safe_cast("abc", int) is None
    assert safe_cast("abc", int, 0) == 0
    
    print("safe_cast tests passed")

def test_safe_int():
    """Test safe_int function."""
    # Test valid integers
    assert safe_int("123") == 123
    assert safe_int(123) == 123
    assert safe_int("-10") == -10
    
    # Test invalid integers
    assert safe_int("abc") is None
    assert safe_int("abc", 0) == 0
    assert safe_int("3.14") is None
    
    print("safe_int tests passed")

def test_safe_float():
    """Test safe_float function."""
    # Test valid floats
    assert safe_float("3.14") == 3.14
    assert safe_float(3.14) == 3.14
    assert safe_float("123") == 123.0
    
    # Test invalid floats
    assert safe_float("abc") is None
    assert safe_float("abc", 0.0) == 0.0
    
    print("safe_float tests passed")

def test_safe_bool():
    """Test safe_bool function."""
    # Test string true values
    assert safe_bool("true") is True
    assert safe_bool("True") is True
    assert safe_bool("yes") is True
    assert safe_bool("y") is True
    assert safe_bool("1") is True
    assert safe_bool("t") is True
    
    # Test string false values
    assert safe_bool("false") is False
    assert safe_bool("False") is False
    assert safe_bool("no") is False
    assert safe_bool("n") is False
    assert safe_bool("0") is False
    assert safe_bool("f") is False
    
    # Test non-string values
    assert safe_bool(True) is True
    assert safe_bool(False) is False
    assert safe_bool(1) is True
    assert safe_bool(0) is False
    
    # Test invalid values
    assert safe_bool("abc") is None
    assert safe_bool("abc", False) is False
    
    print("safe_bool tests passed")

if __name__ == "__main__":
    test_safe_cast()
    test_safe_int()
    test_safe_float()
    test_safe_bool()
    print("All tests passed!") 