from setuptools import setup, find_packages

setup(
    name="cpl-standard",
    version="1.0.0",
    description="Common Prompt Language (CPL) Specification & SDK",
    author="Mahaakali CSIG & Open Source Contributors",
    packages=find_packages(),
    install_packages=[],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: Apache Software License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
