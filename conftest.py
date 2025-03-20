import os
import sys
import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("pytest_debug")

# Log system information
logger.info("Python version: %s", sys.version)
logger.info("Python executable: %s", sys.executable)
logger.info("Platform: %s", sys.platform)

# Add the project root directory to the Python path
project_root = str(Path(__file__).parent.absolute())
logger.info("Project root: %s", project_root)

if project_root not in sys.path:
    logger.info("Adding project root to sys.path")
    sys.path.insert(0, project_root)

# Also add the plexomatic package directory explicitly
package_dir = os.path.join(project_root, "plexomatic")
logger.info("Package directory: %s", package_dir)

if package_dir not in sys.path:
    logger.info("Adding package directory to sys.path")
    sys.path.insert(0, package_dir)

# Log current sys.path for debugging
logger.info("sys.path: %s", json.dumps(sys.path, indent=2))

# Log environment variables
logger.info("PYTHONPATH: %s", os.environ.get("PYTHONPATH", "Not set"))

# Import the main package to verify it can be found
try:
    import plexomatic

    logger.info("Successfully imported plexomatic package")
    logger.info("plexomatic.__file__: %s", plexomatic.__file__)
except ImportError as e:
    logger.error("Failed to import plexomatic package: %s", e)


def pytest_configure(config):
    """
    Pytest hook to configure test environment.
    This runs before tests are collected.
    """
    logger.info("pytest_configure hook called")

    # Print all loaded plugins
    logger.info("Loaded pytest plugins: %s", config.pluginmanager.list_plugin_distinfo())

    # Log where pytest is looking for tests
    logger.info("Test paths: %s", config.getini("testpaths"))


def pytest_collect_file(parent, file_path):
    """
    Pytest hook that runs during test collection.
    Log each file being considered for test collection.
    """
    logger.debug("Collecting file: %s", file_path)
    return None  # Let pytest's default collection continue


def pytest_itemcollected(item):
    """
    Pytest hook that runs when a test item is collected.
    Log each collected test function.
    """
    logger.debug("Collected test: %s", item.nodeid)


def pytest_runtest_setup(item):
    """
    Pytest hook that runs before each test.
    Log each test that's about to be executed.
    """
    logger.info("Setting up test: %s", item.nodeid)


def pytest_runtest_teardown(item):
    """
    Pytest hook that runs after each test.
    Log when a test has completed.
    """
    logger.info("Completed test: %s", item.nodeid)
