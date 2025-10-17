"""
Setup-Skript für den OParl-Client des Bonner Ratsinformationssystems
"""

from setuptools import setup, find_packages
import pathlib

# Lies die README für die lange Beschreibung
here = pathlib.Path(__file__).parent.resolve()
long_description = (here / "README.md").read_text(encoding="utf-8")

setup(
    name="oparl-bonn-client",
    version="1.0.0",
    description="Robuster Python-Client für die OParl-API des Bonner Ratsinformationssystems",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/oparl-bonn-client",
    author="Your Name",
    author_email="your.email@example.com",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    keywords="oparl, api, client, bonn, ratsinformationssystem, open-data",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.9, <4",
    install_requires=[
        "requests>=2.31.0",
        "tqdm>=4.66.0",
        "python-dateutil>=2.8.2",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-mock>=3.11.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "mypy>=1.5.0",
            "types-requests>=2.31.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "oparl-bonn=main:main",
        ],
    },
    project_urls={
        "Bug Reports": "https://github.com/your-username/oparl-bonn-client/issues",
        "Source": "https://github.com/your-username/oparl-bonn-client",
        "Documentation": "https://github.com/your-username/oparl-bonn-client/blob/main/README.md",
    },
)
