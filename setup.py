from setuptools import setup, find_packages

setup(
    name="opbin-api",
    version="1.0.0",
    description="Biblioteca SDK profissional Python para automação e negociação na corretora OpBin / IQ Option.",
    author="Manoel",
    packages=find_packages(),
    install_requires=[
        "requests>=2.28.0",
        "websocket-client>=1.6.0",
        "python-dotenv>=1.0.0",
    ],
    python_requires=">=3.8",
)
