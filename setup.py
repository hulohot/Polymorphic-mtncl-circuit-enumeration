from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="mtncl-circuit-generator",
    version="0.1.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="A tool for generating MTNCL circuits from boolean equations",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/mtncl-circuit-generator",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Electronic Design Automation (EDA)",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=[
        "typing-extensions>=4.0.0",
        "pytest>=7.0.0",
        "pyverilog>=1.3.0",
        "antlr4-python3-runtime>=4.9.0",
        "networkx>=2.6.0",
        "numpy>=1.21.0",
    ],
    entry_points={
        "console_scripts": [
            "mtncl-generate=mtncl_generator.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "mtncl_generator": ["gates/*.vhdl"],
    },
) 