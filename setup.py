from setuptools import setup, find_packages

setup(
    name="policy-checker",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    entry_points={"console_scripts": ["policy-checker=cli:main"]},
    python_requires=">=3.8",
)
