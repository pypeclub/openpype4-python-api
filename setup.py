import os
from setuptools import setup

REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
README_PATH = os.path.join(REPO_ROOT, "README.md")
VERSION_PATH = os.path.join(REPO_ROOT, "ayon_api", "version.py")
_version_content = {}
exec(open(VERSION_PATH).read(), _version_content)

setup(
    name="ayon-python-api",
    version=_version_content["__version__"],
    py_modules=["ayon_api"],
    packages=["ayon_api"],
    author="ynput.io",
    author_email="info@ynput.io",
    license="Apache License (2.0)",
    description="AYON Python API",
    long_description=open(README_PATH).read(),
    long_description_content_type="text/markdown",
    url="https://github.com/ynput/ayon-python-api",
    include_package_data=True,
    # https://pypi.org/classifiers/
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
    ],
    install_requires=[
        "requests >= 2.27.1",
        "six >= 1.15",
        "Unidecode >= 1.3.6",
        "appdirs @ git+https://github.com/ActiveState/appdirs.git@master",
    ],
    dependency_links=[
        "appdirs @ git+https://github.com/ActiveState/appdirs.git@master"
    ],
    keywords=["AYON", "ynput", "OpenPype", "vfx"],
)