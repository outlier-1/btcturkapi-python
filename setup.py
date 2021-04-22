import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="btcturk_api",
    version="1.8.1",
    author="Ömer Miraç Baydemir",
    author_email="omermirac59@gmail.com",
    description="BTCTurk Rest API Python Implementation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/outlier-1/btcturkapi-python",
    packages=['btcturk_api'],
    include_package_data=True,
    install_requires=['requests'],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)
