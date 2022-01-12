import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="basiscore-edge",
    version="2.2.4",
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
    #package_dir={"": "basiscore"},
    packages=setuptools.find_packages(exclude=["test", "app-env", ".vscode"]),
    python_requires=">=3.9.5",
    setup_requires=['wheel']
)
