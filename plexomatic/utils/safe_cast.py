"""Safe casting functions for Python 3.8 compatibility.

This module provides utility functions for safely casting
between different types, especially for older Python versions.
"""

# mypy: disable-error-code="call-arg,unused-ignore,return-value"

from typing import Any, TypeVar, Type, Optional

T = TypeVar("T")


def safe_cast(value: Any, target_type: Type[T], default: Optional[T] = None) -> Optional[T]:
    """Safely cast a value to a target type.

    Args:
        value: The value to cast
        target_type: The type to cast to
        default: Default value to return if casting fails

    Returns:
        The cast value or the default if casting fails
    """
    if value is None:
        return default

    try:
        result = target_type(value)
        return result
    except (ValueError, TypeError, OverflowError):
        return default


def safe_int(value: Any, default: Optional[int] = None) -> Optional[int]:
    """Safely cast a value to an integer.

    Args:
        value: The value to cast
        default: Default value to return if casting fails

    Returns:
        The cast integer or the default if casting fails
    """
    return safe_cast(value, int, default)


def safe_float(value: Any, default: Optional[float] = None) -> Optional[float]:
    """Safely cast a value to a float.

    Args:
        value: The value to cast
        default: Default value to return if casting fails

    Returns:
        The cast float or the default if casting fails
    """
    return safe_cast(value, float, default)


def safe_bool(value: Any, default: Optional[bool] = None) -> Optional[bool]:
    """Safely cast a value to a boolean.

    Args:
        value: The value to cast
        default: Default value to return if casting fails

    Returns:
        The cast boolean or the default if casting fails
    """
    if isinstance(value, str):
        value = value.lower()
        if value in ("true", "yes", "y", "1", "t"):
            return True
        if value in ("false", "no", "n", "0", "f"):
            return False
        return default
    return safe_cast(value, bool, default)
