import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="mtrpacket",
    version="1.0.0",
    python_requires=">=3.5",
    author="Matt Kimball",
    author_email="matt.kimball@gmail.com",
    description="Asynchronous network probes for Python",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/matt-kimball/mtr-packet-python",
    packages=setuptools.find_packages(),
    classifiers=[
        "Topic :: System :: Networking",
        "Framework :: AsyncIO",
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
    ],
)
