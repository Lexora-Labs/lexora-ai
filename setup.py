from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="lexora-ai",
    version="0.1.0",
    author="Lexora Labs",
    description="AI-powered eBook translation tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.8",
    install_requires=[
        "openai>=1.0.0",
        "azure-ai-inference>=1.0.0b1",
        "ebooklib>=0.18",
        "mobi>=0.3.3",
        "python-docx>=1.0.0",
        "markdown>=3.5",
        "beautifulsoup4>=4.12.0",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "lexora=lexora.cli:main",
        ],
    },
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
)
