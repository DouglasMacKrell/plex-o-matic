import os
import sys
from pathlib import Path

# Add the project root directory to the Python path
# This ensures that imports in tests will work correctly regardless of where pytest is executed from
project_root = str(Path(__file__).parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Also add the plexomatic package directory explicitly
package_dir = os.path.join(project_root, "plexomatic")
if package_dir not in sys.path:
    sys.path.insert(0, package_dir)
