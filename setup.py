from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name='Linode-DB',
    version='0.1',
    packages=find_packages(),
    install_requires=requirements,
    package_data={
        "app": [
            "data/*",
        ],
    },
    include_package_data=True,
    author="Sabyasachi Seal"
)