#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""Setup script."""

# Copyright (c) 2025 SUSE LLC
#
# This file is part of aws-mp-utils. aws-mp-utils provides an
# api and command line utilities for handling marketplace catalog API
# in the AWS Cloud.
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

from setuptools import find_packages, setup

with open('README.md') as readme_file:
    readme = readme_file.read()

with open('requirements.txt') as req_file:
    requirements = req_file.read().splitlines()

with open('requirements-test.txt') as req_file:
    test_requirements = req_file.read().splitlines()[2:]

with open('requirements-dev.txt') as req_file:
    dev_requirements = test_requirements + req_file.read().splitlines()[2:]


setup(
    name='aws-mp-utils',
    version='0.1.0',
    description='Package that provides utilities for '
                'handling Marketplace Catalog API in AWS Cloud.',
    long_description=readme,
    long_description_content_type='text/markdown',
    author='SUSE',
    author_email='public-cloud-dev@susecloud.net',
    url='https://github.com/SUSE-Enceladus/aws-mp-utils',
    packages=find_packages(),
    package_dir={
        'aws_mp_utils': 'aws_mp_utils'
    },
    entry_points={
        'console_scripts': [
            'aws-mp-utils=aws_mp_utils.scripts.cli:main'
        ]
    },
    include_package_data=True,
    python_requires='>=3.9',
    install_requires=requirements,
    extras_require={
        'dev': dev_requirements,
        'test': test_requirements
    },
    license='GPLv3+',
    zip_safe=False,
    keywords='aws-mp-utils aws_mp_utils',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Topic :: System :: Software Distribution',
        'License :: OSI Approved :: '
        'GNU General Public License v3 or later (GPLv3+)',
        'Natural Language :: English',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Programming Language :: Python :: 3.12',
        'Programming Language :: Python :: 3.13',
    ],
)
