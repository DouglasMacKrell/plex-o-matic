"""Safe casting utility.

This module provides a utility function for safely casting values from one type to another.
"""

from typing import TypeVar, Type, Optional, Any, cast

# Type variable for input
T = TypeVar("T")


def safe_cast(t: Type[T], val: Any, default: Optional[T] = None) -> Optional[T]:
    """Safely cast a value to a specified type.

    Args:
        t: The target type to cast to
        val: The value to cast
        default: The default value to return if casting fails

    Returns:
        The cast value if successful, otherwise the default value
    """
    try:
        # Special case for bool to handle string values correctly
        if t is bool and isinstance(val, str):
            return cast(Optional[T], val.lower() in ("true", "yes", "1", "y", "t"))

        # Special case for casting to int from float
        if t is int and isinstance(val, float):
            return cast(Optional[T], int(val))

        # Special case for casting None to appropriate types
        if val is None:
            if t is str:
                return cast(Optional[T], "")
            elif t is int:
                return cast(Optional[T], 0)
            elif t is float:
                return cast(Optional[T], 0.0)
            elif t is bool:
                return cast(Optional[T], False)
            elif t is list:
                return cast(Optional[T], [])
            elif t is dict:
                return cast(Optional[T], {})
            else:
                return default

        # Normal type conversion
        result = t(val)
        return cast(Optional[T], result)
    except (ValueError, TypeError, AttributeError, OverflowError):
        return default
