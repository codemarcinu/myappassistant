from setuptools import setup, find_packages

setup(
    name="foodsave-backend",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "alembic",
        "python-multipart",
        "python-jose[cryptography]",
        "passlib[bcrypt]",
        "pydantic",
        "pydantic-settings",
    ],
) 