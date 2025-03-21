#!/usr/bin/env python
"""
Debug script to test imports and report any issues.
This helps diagnose CI failures related to imports.
"""

import sys
import importlib
from pathlib import Path


def print_section(title):
    """Print a section header for better readability."""
    print("\n" + "=" * 50)
    print(f" {title} ".center(50, "="))
    print("=" * 50)


def test_import(module_name, *, from_package=None, import_name=None):
    """Test importing a module or object and report the result."""
    status = "✓"
    error = None

    try:
        if from_package:
            # Import something from a package (from X import Y)
            module = importlib.import_module(from_package)
            if hasattr(module, import_name):
                getattr(module, import_name)
            else:
                status = "✗"
                error = f"Attribute '{import_name}' not found in module '{from_package}'"
        else:
            # Simple module import
            importlib.import_module(module_name)
    except Exception as e:
        status = "✗"
        error = str(e)

    if error:
        print(f"{status} {module_name}: FAILED - {error}")
        return False
    else:
        print(f"{status} {module_name}: OK")
        return True


def find_python_files(directory, pattern="*.py"):
    """Find all Python files in the given directory."""
    directory = Path(directory)
    return sorted(directory.glob(f"**/{pattern}"))


def check_python_version():
    """Check Python version details."""
    print(f"Python version: {sys.version}")
    print(f"Python implementation: {sys.implementation}")
    print(f"Python path: {sys.executable}")
    print("Python path entries:")
    for i, path in enumerate(sys.path):
        print(f"  {i+1}. {path}")


def check_typing_support():
    """Check support for various typing features."""
    print_section("TYPING SUPPORT")

    typing_features = [
        "List",
        "Dict",
        "Tuple",
        "Optional",
        "Union",
        "Any",
        "TypeVar",
        "Protocol",
        "Literal",
        "TypedDict",
        "Final",
        "Annotated",
    ]

    for feature in typing_features:
        try:
            # Try importing from typing
            exec(f"from typing import {feature}")
            print(f"✓ typing.{feature}: OK")
        except ImportError:
            try:
                # Try importing from typing_extensions
                exec(f"from typing_extensions import {feature}")
                print(f"✓ typing_extensions.{feature}: OK")
            except ImportError:
                print(f"✗ {feature}: NOT AVAILABLE")


def check_core_modules():
    """Check core plexomatic modules."""
    print_section("CORE MODULES")

    modules = [
        "plexomatic",
        "plexomatic.core",
        "plexomatic.utils",
        "plexomatic.api",
        "plexomatic.cli",
    ]

    for module in modules:
        test_import(module)


def check_important_classes():
    """Check important classes and objects."""
    print_section("IMPORTANT CLASSES")

    classes = [
        ("MediaType", "plexomatic.core.models"),
        ("Template", "plexomatic.utils.name_templates"),
        ("NameParser", "plexomatic.utils.name_parser"),
    ]

    for class_name, module_name in classes:
        test_import(class_name, from_package=module_name, import_name=class_name)


def check_enum_values():
    """Check enum values for important enums."""
    print_section("ENUM VALUES")

    try:
        from plexomatic.core.models import MediaType

        print("MediaType enum values:")
        for name, value in MediaType.__members__.items():
            print(f"  - {name} = {value}")
    except ImportError as e:
        print(f"Could not check MediaType enum: {e}")

    try:
        from plexomatic.utils.name_templates import TemplateType

        print("\nTemplateType enum values:")
        for name, value in TemplateType.__members__.items():
            print(f"  - {name} = {value}")
    except ImportError as e:
        print(f"Could not check TemplateType enum: {e}")


def main():
    """Run all diagnostic checks."""
    print_section("SYSTEM INFO")
    check_python_version()

    check_typing_support()
    check_core_modules()
    check_important_classes()
    check_enum_values()

    print_section("SUMMARY")
    print("Debug diagnostics completed. Check output for any errors.")


if __name__ == "__main__":
    main()
