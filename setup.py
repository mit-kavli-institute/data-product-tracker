#!/usr/bin/env python

"""The setup script."""

from setuptools import find_packages, setup

with open("README.rst") as readme_file:
    readme = readme_file.read()

with open("HISTORY.rst") as history_file:
    history = history_file.read()

requirements = [
    "Click>=7.0",
]

test_requirements = [
    "pytest>=3",
]

setup(
    author="William Christopher Fong",
    author_email="willfong@mit.edu",
    python_requires=">=3.6",
    classifiers=[
        "Development Status :: 2 - Pre-Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    description=(
        "An interface to track various data products and their dependencies "
        "and environments."
    ),
    entry_points={
        "console_scripts": [
            "data_product_tracker=data_product_tracker.cli:main",
        ],
    },
    install_requires=requirements,
    license="MIT license",
    long_description=readme + "\n\n" + history,
    include_package_data=True,
    keywords="data_product_tracker",
    name="data_product_tracker",
    packages=find_packages(
        include=["data_product_tracker", "data_product_tracker.*"]
    ),
    test_suite="tests",
    tests_require=test_requirements,
    url="https://github.com/WilliamCFong/data_product_tracker",
    version="0.1.3",
    zip_safe=False,
)
