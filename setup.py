import setuptools

from bclib import __version__

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="bclib",
    version=__version__,
    author="Manzoomeh Negaran",
    author_email="info@manzoomeh.ir",
    description="Python base gateway for communicate with basiscore webserver",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Manzoomeh/BasisCore.Server.Edge/wiki",
    project_urls={
        "Bug Tracker": "https://github.com/Manzoomeh/BasisCore.Server.Edge/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    license="MIT",
    install_requires=[
        "aio-pika",
        "pika",
        "pymongo",
        "pyodbc",
        "aiohttp",
        "cryptography",
        "certifi",
    ],
    packages=setuptools.find_packages(exclude=["tests", "examples", "app-env", ".vscode"]),
    python_requires=">=3.13",
    extras_require={
        "dev": [
            "pytest>=8.0",
        ],
    },
    setup_requires=["wheel"],
)
