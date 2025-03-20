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
import os
import sys
import logging
from pathlib import Path

# Configure logging for tests
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s [TESTS] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("pytest_tests_debug")

# Log test environment information
logger.info("Tests conftest.py loaded")
logger.info("Python version: %s", sys.version)
logger.info("Python executable: %s", sys.executable)

# Add parent directory to sys.path to ensure imports work
project_root = str(Path(__file__).parent.parent.absolute())
logger.info("Project root from tests: %s", project_root)

if project_root not in sys.path:
    logger.info("Adding project root to sys.path from tests conftest")
    sys.path.insert(0, project_root)


# Log current directory structure for debugging
def log_directory_structure(path, prefix=""):
    """Log the directory structure recursively for debugging"""
    if prefix == "":
        logger.info("Directory structure of %s:", path)

    try:
        content = os.listdir(path)
        for item in sorted(content):
            item_path = os.path.join(path, item)
            if os.path.isdir(item_path) and not item.startswith(".") and item != "__pycache__":
                logger.info("%s[DIR] %s", prefix, item)
                log_directory_structure(item_path, prefix + "  ")
            elif item.endswith(".py"):
                logger.info("%s[PY] %s", prefix, item)
    except Exception as e:
        logger.error("Error reading directory %s: %s", path, e)


# Log the test directory structure
log_directory_structure(os.path.dirname(__file__))


# Test imports of key modules
def test_import(module_name):
    """Test importing a module and log the result"""
    try:
        module = __import__(module_name)
        logger.info("Import SUCCESS: %s at %s", module_name, getattr(module, "__file__", "unknown"))
        return True
    except ImportError as e:
        logger.error("Import FAILED: %s - %s", module_name, e)
        return False


# Test important imports
for module in [
    "plexomatic",
    "plexomatic.cli",
    "pytest",
    "tests",
]:
    test_import(module)


# Ensure that tests in the package can import from parent directory
sys.path.insert(0, str(Path(__file__).parent.parent))


# Define a fixture that will be available to all tests
def pytest_configure(config):
    """Pytest configuration hook"""
    logger.info("Pytest configuration hook called in tests/conftest.py")
    logger.info("Test collection directories: %s", config.getini("testpaths"))


def pytest_collection_modifyitems(config, items):
    """Called after test collection - logs number of collected tests"""
    logger.info("Collected %d tests", len(items))
    for idx, item in enumerate(items[:10]):  # Log first 10 tests
        logger.info("Test %d: %s", idx + 1, item.nodeid)


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
