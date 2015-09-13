#!/usr/bin/env python
# # coding: utf-8

from setuptools import setup
from abe import __version__

setup(
    name='abe-python',
    description='Parse ABE files for usage within python tests',
    version=__version__,
    author='Carles Barrobés',
    author_email='carles@barrobes.com',
    url='https://github.com/apibyexample/abe-python',
    packages=['abe'],
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Software Development :: Testing',
    ],
    install_requires=[
        'supermutes>=0.2.5',
    ]
)
