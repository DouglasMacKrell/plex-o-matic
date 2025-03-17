"""Configuration for pytest with type annotations support."""

from typing import Any, Callable, List, Optional, TypeVar, Union, cast, overload
import pytest

T = TypeVar("T")
F = TypeVar("F", bound=Callable[..., Any])
P = TypeVar("P")


# Properly typed fixture decorator
@overload
def fixture(function: Callable[[], T]) -> Callable[[], T]: ...


@overload
def fixture(function: Callable[[Any], T]) -> Callable[[Any], T]: ...


@overload
def fixture(
    *,
    scope: str = "function",
    params: Optional[List[Any]] = None,
    autouse: bool = False,
    ids: Optional[List[str]] = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]: ...


def fixture(
    function: Optional[Callable[..., T]] = None,
    *,
    scope: str = "function",
    params: Optional[List[Any]] = None,
    autouse: bool = False,
    ids: Optional[List[str]] = None,
) -> Any:
    """Typed version of pytest.fixture decorator."""
    if function:
        return pytest.fixture(function)
    return pytest.fixture(scope=scope, params=params, autouse=autouse, ids=ids)


# Properly typed parametrize decorator
def parametrize(
    argnames: Union[str, List[str]],
    argvalues: List[Any],
    indirect: bool = False,
    ids: Optional[List[str]] = None,
    scope: Optional[str] = None,
) -> Callable[[F], F]:
    """Typed version of pytest.mark.parametrize decorator."""
    decorator = pytest.mark.parametrize(
        argnames=argnames, argvalues=argvalues, indirect=indirect, ids=ids, scope=scope
    )
    return cast(Callable[[F], F], decorator)


# Create a typed mark namespace
class TypedMark:
    """Typed mark namespace for pytest."""

    @staticmethod
    def parametrize(
        argnames: Union[str, List[str]],
        argvalues: List[Any],
        indirect: bool = False,
        ids: Optional[List[str]] = None,
        scope: Optional[str] = None,
    ) -> Callable[[F], F]:
        """Typed version of pytest.mark.parametrize decorator."""
        return parametrize(argnames, argvalues, indirect, ids, scope)

    def __getattr__(self, name: str) -> Any:
        """Pass through to pytest.mark for other attributes."""
        return getattr(pytest.mark, name)


# Create instance of TypedMark
mark = TypedMark()
