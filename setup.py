from setuptools import find_packages, setup

extras_require = {
    "dev": [
        "pre-commit",
        "black",
    ],
    "test": [],
}
with open("README.MD") as f:
    long_description = f.read()

setup(
    name="archivooor",
    version="0.0.3",
    description="A Python package to submit web pages to the Wayback Machine for archiving.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Barabazs",
    url="https://github.com/Barabazs/archivooor",
    license="MIT",
    packages=find_packages(exclude=["tests", "tests.*"]),
    install_requires=[
        "requests>=2.28.1",
        "urllib3>=1.26.12",
        "python-dotenv==0.21.0",
    ],
    extras_require=extras_require,
    classifiers=[
        "Development Status :: 3 - Alpha",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: English",
        "Programming Language :: Python :: 3 :: Only",
    ],
)
