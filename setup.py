from setuptools import setup, find_packages

setup(
    name="nql",
    version="1.0.0",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "nql": [
            "ml/models/*.pt",
            "ml/data/*.json",
            "ml/data/*.jsonl",
        ]
    },
    install_requires=[
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "rapidfuzz",
        "pydantic",
    ],
    author="Gemini CLI",
    description="A lightweight offline Natural Language to SQL engine",
    python_requires=">=3.11",
)
