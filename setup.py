import setuptools
from dawgmon.version import VERSION

with open("README", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="dawgmon-gvb",
    version=VERSION,
    author="Anvil Ventures",
    author_email="info@anvilventures.com",
    description="Monitor operating system changes and analyze "
                "introduced attack surface when installing software",
    long_description=long_description,
    long_description_content_type="text/plain",
    url="https://github.com/anvilventures/dawgmon",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Development Status :: 5 - Production/Stable",
        "Operating System :: POSIX :: Linux",
        "Operating System :: POSIX :: Other",
        "Programming Language :: Python :: 3 :: Only",
        "Topic :: System :: Monitoring",
        "Topic :: System :: Systems Administration",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.6",
    ],
    python_requires=">=3.6",
    entry_points = {
        "console_scripts": ["dawgmon=dawgmon.dawgmon:main"],
    }
)
