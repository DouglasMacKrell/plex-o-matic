#!/usr/bin/env python
"""Setup script for plexomatic."""

from setuptools import setup, find_packages

# Define package metadata
setup(
    name="plex-o-matic",
    version="0.2.0",
    description="An intelligent media file organization tool for Plex",
    author="Douglas MacKrell",
    author_email="your.email@example.com",
    # Include all packages and subpackages
    packages=find_packages(include=["plexomatic", "plexomatic.*", "tests", "tests.*"]),
    # Include package data
    package_data={
        "": ["*.yaml", "*.yml", "*.json", "*.txt"],
    },
    # Define dependencies
    install_requires=[
        "click>=8.1.0",
        "rich>=13.0.0",
        "pathlib>=1.0.1",
        "requests>=2.31.0",
        "pyyaml>=6.0.1",
        "sqlalchemy>=2.0.0",
        "python-dotenv>=1.0.0",
        "typing_extensions>=4.0.0",
    ],
    # Define extra dependencies
    extras_require={
        "test": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "pytest-mock>=3.11.1",
        ],
        "dev": [
            "black>=23.7.0",
            "ruff>=0.0.284",
            "mypy>=1.5.1",
        ],
    },
    # Define entry points
    entry_points={
        "console_scripts": [
            "plexomatic=plexomatic.cli:cli",
        ],
    },
    # Python requirements
    python_requires=">=3.8",
    # Metadata
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
