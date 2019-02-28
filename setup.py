import setuptools

with open("README.md","r") as fr:
    full_description = fr.read()

setuptools.setup(

    name="emgeecore",
    version="0.0.1",
    author="dMacGit",
    author_email="d.g.mcindoe@gmail.com",
    description="Core logic for emgee (Media Grabber) application",
    long_description=full_description,
    long_description_content_type="text/markdown",
    url="https://github.com/dMacGit/emgee_core",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],

)
