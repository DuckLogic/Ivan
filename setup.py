from setuptools import setup, find_namespace_packages

setup(
    name="ivan",
    version="0.1.0",
    package_dir={"": "src"},
    packages=find_namespace_packages(where="src"),
)
