from setuptools import setup

with open("README.MD") as f:
    long_description = f.read()

setup(
    name="archivooor",
    version="0.0.2",
    description="A Python package to submit web pages to the Wayback Machine for archiving.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Barabazs",
    url="https://github.com/Barabazs/archivooor",
    license="MIT",
    packages=["archivooor"],
    install_requires=[
        "requests>=2.27.1",
        "urllib3>=1.26.9",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3 :: Only",
    ],
)
