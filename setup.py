from setuptools import setup, find_packages


with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="mtgc",
    version="0.1",
    packages=find_packages(),
    entry_points={
        "console_scripts": [
            "mtgc=mtgc.cli.main:main",
        ],
    },
    install_requires=requirements,
)
