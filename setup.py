#!/usr/bin/env python
"""Setup script for plexomatic."""

from setuptools import setup, find_packages

if __name__ == "__main__":
    setup(
        name="plex-o-matic",
        version="0.2.0",
        description="An intelligent media file organization tool for Plex",
        author="Douglas MacKrell",
        author_email="your.email@example.com",
        packages=find_packages(),
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
        entry_points={
            "console_scripts": [
                "plexomatic=plexomatic.cli:cli",
            ],
        },
        python_requires=">=3.8",
    )
