#!/usr/bin/env python3

"""
Setup script for cdp_pipeline library.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text() if readme_file.exists() else ""

setup(
    name="cdp_pipeline",
    version="0.1.0",
    description="A Python library for composing CDP audio processing workflows",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/cdp_pipeline",
    packages=find_packages(),
    install_requires=[
        "sh>=2.0.0",
    ],
    extras_require={
        "cli": ["click>=8.0.0"],
        "dev": [
            "ipython>=9.0.0",
            "pytest>=7.0.0",
        ],
    },
    python_requires=">=3.7",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Topic :: Multimedia :: Sound/Audio",
        "Topic :: Multimedia :: Sound/Audio :: Analysis",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    keywords="cdp audio processing pipeline spectral",
    entry_points={
        "console_scripts": [
            "cdp-interleave=interleave_v2:main",
        ],
    },
)
