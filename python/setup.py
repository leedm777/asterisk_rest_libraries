#!/usr/bin/env python

#
# Copyright (c) 2013, Digium, Inc.
#

import os

from setuptools import setup

setup(
    name="asterisk-rest-library",
    version="0.0.1",
    license="BSD 3-Clause License",
    description="Library for accessing the Asterisk REST Interface",
    long_description=open(os.path.join(os.path.dirname(__file__),
                                       "README.md")).read(),
    author="Digium, Inc.",
    url="https://github.com/asterisk/asterisk_rest_libraries",
    packages=["ari"],
    classifiers=[
        "Development Status :: 1 - Planning",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
    ],
    setup_requires=["nose>=1.3", "tissue"],
    tests_require=["coverage", "httpretty"],
    install_requires=["swaggerpy"],
)
