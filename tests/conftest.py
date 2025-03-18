"""Test configuration and fixtures."""

from typing import (
    Any,
    Callable,
    Iterable,
    List,
    Literal,
    Optional,
    Sequence,
    TypeVar,
    Union,
    cast,
    overload,
)

import pytest
from _pytest.config import Config

# Type variables for better typing
T = TypeVar("T")
F = TypeVar("F", bound=Callable[..., Any])
FixtureScope = Literal["session", "package", "module", "class", "function"]
IdType = Union[str, float, int, bool, None]


@overload
def fixture(function: Callable[..., T]) -> Callable[..., T]: ...


@overload
def fixture(
    *,
    scope: Union[FixtureScope, Callable[[str, Config], FixtureScope]] = "function",
    params: Optional[Iterable[Any]] = None,
    autouse: bool = False,
    ids: Optional[Union[Sequence[Optional[object]], Callable[[Any], Optional[object]]]] = None,
) -> Callable[[Callable[..., T]], Callable[..., T]]: ...


def fixture(
    function: Optional[Callable[..., T]] = None,
    *,
    scope: Union[FixtureScope, Callable[[str, Config], FixtureScope]] = "function",
    params: Optional[Iterable[Any]] = None,
    autouse: bool = False,
    ids: Optional[Union[Sequence[Optional[object]], Callable[[Any], Optional[object]]]] = None,
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
    ids: Optional[Union[Iterable[IdType], Callable[[Any], Optional[object]]]] = None,
    scope: Optional[FixtureScope] = None,
) -> Callable[[F], F]:
    """Typed version of pytest.mark.parametrize decorator."""
    decorator = pytest.mark.parametrize(
        argnames=argnames, argvalues=argvalues, indirect=indirect, ids=ids, scope=scope
    )
    return cast(Callable[[F], F], decorator)


# Create a typed mark namespace
class TypedMark:
    """Typed mark namespace for pytest decorators."""

    @staticmethod
    def parametrize(
        argnames: Union[str, List[str]],
        argvalues: List[Any],
        indirect: bool = False,
        ids: Optional[Union[Iterable[IdType], Callable[[Any], Optional[object]]]] = None,
        scope: Optional[FixtureScope] = None,
    ) -> Callable[[F], F]:
        """Typed version of pytest.mark.parametrize."""
        decorator = pytest.mark.parametrize(
            argnames=argnames, argvalues=argvalues, indirect=indirect, ids=ids, scope=scope
        )
        return cast(Callable[[F], F], decorator)

    def __getattr__(self, name: str) -> Any:
        """Get any other mark from pytest.mark."""
        return getattr(pytest.mark, name)


# Create a typed instance of the mark namespace
mark = TypedMark()
