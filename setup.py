from setuptools import setup, find_packages

setup(
    name="borneoai",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "rich>=13.0.0",
        "prompt_toolkit>=3.0.0",
    ],
    entry_points={
        "console_scripts": [
            "borneoai = borneoai.cli:main",
        ],
    },
    author="BorneoAI Team",
    description="A powerful Python-based CLI Coding Agent powered by Gemini REST API",
)
