from setuptools import find_packages, setup

setup(
    name="wallet-vault",
    version="0.1.0",
    packages=find_packages(),
    python_requires=">=3.10",
    install_requires=[
        "python-dotenv>=1.0.0",
        "fastapi>=0.115.0",
        "uvicorn>=0.30.0",
        "bcrypt>=4.0.0",
        "itsdangerous>=2.0.0",
        "requests>=2.31.0",
        "cryptography>=42.0.0",
        "embit>=0.8.0",
        "mnemonic>=0.21",
    ],
    extras_require={
        "dev": ["pytest>=8.0.0"],
    },
)
