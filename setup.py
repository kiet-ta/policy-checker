from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

setup(
    name="policy-checker",
    version="0.3.0",
    author="kiet-ta",
    author_email="trananhkiet21082005@gmail.com",
    description="CLI tool to validate mobile apps against App Store and Google Play policies with image processing",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/kiet-ta/policy-checker",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Software Development :: Quality Assurance",
        "Topic :: Multimedia :: Graphics :: Graphics Conversion",
    ],
    python_requires=">=3.9",
    install_requires=[
        "pyyaml>=6.0",
        "click>=8.0",
        "rich>=13.0",
        "requests>=2.28",
        "beautifulsoup4>=4.12",
        "Pillow>=10.0.0",
        "numpy>=1.24.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "ruff>=0.1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "policy-checker=cli:main",
        ],
    },
)
