"""Tests for the safe_cast module."""

from typing import Any, TypeVar

from plexomatic.utils.safe_cast import safe_cast, safe_int, safe_float, safe_bool

T = TypeVar("T")


class TestSafeCast:
    """Test cases for the safe_cast function."""

    def test_successful_cast(self) -> None:
        """Test casting a value successfully."""
        # Integer casting
        assert safe_cast("123", int) == 123
        assert safe_cast(123.5, int) == 123
        assert safe_cast(True, int) == 1

        # Float casting
        assert safe_cast("123.5", float) == 123.5
        assert safe_cast(123, float) == 123.0

        # String casting
        assert safe_cast(123, str) == "123"
        assert safe_cast(123.5, str) == "123.5"
        assert safe_cast(True, str) == "True"

        # Boolean casting
        assert safe_cast(1, bool) is True
        assert safe_cast(0, bool) is False

    def test_failed_cast(self) -> None:
        """Test handling of failed casts."""
        # Integer casting failures
        assert safe_cast("abc", int) is None
        assert safe_cast("123.5", int, 0) == 0  # Would fail without default

        # Float casting failures
        assert safe_cast("abc", float) is None
        assert safe_cast("abc", float, 0.0) == 0.0

        # Complex failures
        complex_obj = object()
        assert safe_cast(complex_obj, int) is None

    def test_none_value(self) -> None:
        """Test casting None values."""
        assert safe_cast(None, int) is None
        assert safe_cast(None, str) is None
        assert safe_cast(None, bool) is None

        # With default values
        assert safe_cast(None, int, 0) == 0
        assert safe_cast(None, str, "default") == "default"
        assert safe_cast(None, bool, False) is False

    def test_with_default(self) -> None:
        """Test casting with default values."""
        assert safe_cast("abc", int, 42) == 42
        assert safe_cast("abc", float, 3.14) == 3.14

        # A better test for default value with str casting
        class CustomClass:
            def __str__(self) -> str:
                return "custom_str"

        # Object without __str__ will use repr and not fail
        obj = object()
        assert isinstance(safe_cast(obj, str), str)

        # For a custom object with __str__, it should use that method
        custom = CustomClass()
        assert safe_cast(custom, str) == "custom_str"

        # Test with a type that can't cast the object at all
        complex_obj = object()
        assert safe_cast(complex_obj, int, 42) == 42

    def test_custom_type(self) -> None:
        """Test casting to a custom type."""

        class CustomType:
            def __init__(self, value: Any) -> None:
                self.value = value

        # Successful casting to custom type
        result = safe_cast(123, CustomType)
        assert isinstance(result, CustomType)
        assert result.value == 123

        # Custom type that raises in __init__
        class FailingType:
            def __init__(self, value: Any) -> None:
                raise ValueError("Always fails")

        assert safe_cast(123, FailingType) is None
        assert safe_cast(123, FailingType, "default") == "default"


class TestSafeInt:
    """Test cases for the safe_int function."""

    def test_successful_cast(self) -> None:
        """Test successful integer casts."""
        assert safe_int("123") == 123
        assert safe_int(123) == 123
        assert safe_int(123.5) == 123
        assert safe_int(True) == 1

    def test_failed_cast(self) -> None:
        """Test failed integer casts."""
        assert safe_int("abc") is None
        assert safe_int("abc", 0) == 0
        assert safe_int(None) is None
        assert safe_int(None, 0) == 0

    def test_edge_cases(self) -> None:
        """Test edge cases for safe_int."""
        assert safe_int("0") == 0
        assert safe_int("-123") == -123

        # Test with infinity, which should fail to convert and return None
        infinity = float("inf")
        assert safe_int(infinity) is None
        assert safe_int(infinity, 999) == 999  # Should return the default


class TestSafeFloat:
    """Test cases for the safe_float function."""

    def test_successful_cast(self) -> None:
        """Test successful float casts."""
        assert safe_float("123.5") == 123.5
        assert safe_float(123) == 123.0
        assert safe_float(123.5) == 123.5
        assert safe_float(True) == 1.0

    def test_failed_cast(self) -> None:
        """Test failed float casts."""
        assert safe_float("abc") is None
        assert safe_float("abc", 0.0) == 0.0
        assert safe_float(None) is None
        assert safe_float(None, 0.0) == 0.0

    def test_edge_cases(self) -> None:
        """Test edge cases for safe_float."""
        assert safe_float("0") == 0.0
        assert safe_float("-123.5") == -123.5
        assert safe_float("inf") == float("inf")
        assert safe_float("-inf") == float("-inf")
        assert isinstance(safe_float("nan"), float)  # NaN doesn't equal itself


class TestSafeBool:
    """Test cases for the safe_bool function."""

    def test_successful_cast(self) -> None:
        """Test successful boolean casts."""
        assert safe_bool(True) is True
        assert safe_bool(False) is False
        assert safe_bool(1) is True
        assert safe_bool(0) is False

    def test_string_values(self) -> None:
        """Test string value conversions."""
        # True values
        assert safe_bool("true") is True
        assert safe_bool("True") is True
        assert safe_bool("TRUE") is True
        assert safe_bool("yes") is True
        assert safe_bool("Yes") is True
        assert safe_bool("y") is True
        assert safe_bool("Y") is True
        assert safe_bool("1") is True
        assert safe_bool("t") is True
        assert safe_bool("T") is True

        # False values
        assert safe_bool("false") is False
        assert safe_bool("False") is False
        assert safe_bool("FALSE") is False
        assert safe_bool("no") is False
        assert safe_bool("No") is False
        assert safe_bool("n") is False
        assert safe_bool("N") is False
        assert safe_bool("0") is False
        assert safe_bool("f") is False
        assert safe_bool("F") is False

    def test_failed_cast(self) -> None:
        """Test failed boolean casts."""
        assert safe_bool("abc") is None
        assert safe_bool("abc", False) is False
        assert safe_bool(None) is None
        assert safe_bool(None, False) is False

    def test_edge_cases(self) -> None:
        """Test edge cases for safe_bool."""
        assert safe_bool([]) is False  # Empty collections are falsy
        assert safe_bool([1, 2, 3]) is True  # Non-empty collections are truthy
        assert safe_bool("") is None  # Empty string doesn't match any pattern
        assert safe_bool("", False) is False  # With default
