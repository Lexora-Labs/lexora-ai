"""
Setup configuration for Lexora AI
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="lexora-ai",
    version="0.1.0",
    author="Lexora Labs",
    author_email="",
    description="AI-Powered eBook Translator for EPUB files",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Lexora-Labs/lexora-ai",
    project_urls={
        "Bug Tracker": "https://github.com/Lexora-Labs/lexora-ai/issues",
        "Source Code": "https://github.com/Lexora-Labs/lexora-ai",
    },
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Linguistic",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.9",
    install_requires=[
        "ebooklib>=0.18",
        "beautifulsoup4>=4.9.0",
        "lxml>=4.6.0",
        "openai>=1.0.0",
        "requests>=2.25.0",
        "python-dotenv>=0.19.0",
    ],
    entry_points={
        "console_scripts": [
            "lexora=lexora.cli:main",
        ],
    },
    keywords="epub translation ai gpt azure openai ebook translator",
    license="Apache License 2.0",
)
