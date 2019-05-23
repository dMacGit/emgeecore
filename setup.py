from setuptools import setup, find_packages

with open("README.md","r") as fr:
    full_description = fr.read()

setup(

    name="emgeecore",
    version="0.0.1",
    author="dMacGit",
    author_email="d.g.mcindoe@gmail.com",
    description="Core logic for emgee (Media Grabber) application",
    long_description=full_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dMacGit/emgeecore",
    packages=find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    install_requires=[
        "meta_core>=1.0",
    ],
    dependency_links=[
        "git+https://github.com/dMacGit/meta_core#egg=meta_core-1.0",
    ]
)
