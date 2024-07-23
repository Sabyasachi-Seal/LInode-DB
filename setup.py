from setuptools import setup, find_packages

setup(
    name='Linode-DB',
    version='0.1',
    packages=find_packages(),
    install_requires=[
        'fastapi',
        'uvicorn',
        'fastapi-users[sqlalchemy2]',
        'fastapi-users[authentication]',
        'fastapi-users[jwt]',
        'sqlalchemy',
        'aiomysql',
        'pydantic',
        'python-dotenv',
        'requests',
    ],
)