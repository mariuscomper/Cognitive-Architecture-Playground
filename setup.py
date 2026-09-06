from pathlib import Path

from setuptools import find_packages, setup


root = Path(__file__).parent
long_description = (root / "README.md").read_text(encoding="utf-8")

setup(
    name="cognitive-architecture-playground",
    version="0.1.0",
    description="A dependency-light symbolic cognitive architecture playground",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(include=["cognitive_arch", "cognitive_arch.*"]),
    python_requires=">=3.8",
    install_requires=[],
)
