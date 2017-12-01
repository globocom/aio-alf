# -*- coding: utf-8 -*-

from setuptools import setup, find_packages
from aioalf import __version__

tests_require = [
    'mock',
    'asynctest',
    'bumpversion',
    'nose',
    'coverage',
    'yanc',
    'ipdb',
    'tox',
    'flake8',
]

setup(
    name='aio-alf',
    version=__version__,
    description="OAuth Client For aiohttp",
    long_description=open('README.rst').read(),
    keywords='oauth client client_credentials aiohtpp',
    author=u'Globo.com',
    author_email='entretenimento1@corp.globo.com',
    url='https://github.com/globocom/aio-alf',
    license='MIT',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: MacOS',
        'Operating System :: POSIX',
        'Operating System :: Unix',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3.6',
    ],
    packages=find_packages(
        exclude=(
            'tests',
        ),
    ),
    include_package_data=True,
    install_requires=[
        'aiohttp>=2.3.0',
    ],
    extras_require={
        'tests': tests_require,
    },
)
