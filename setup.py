# -*- encoding: utf8 -*-
from setuptools import setup, find_packages

import os
import io

def read(*names, **kwargs):
    return io.open(
        os.path.join(os.path.dirname(__file__), *names),
        encoding=kwargs.get('encoding', 'utf8')
    ).read()

setup(
    name='GitSync',
    version='0.1.2',
    author='Jachin Rupe',
    author_email='jachin@clockwork.net',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    scripts=['bin/git_sync'],
    include_package_data=True,
    zip_safe=False,
    url='http://pypi.python.org/pypi/GitSync/',
    license='LICENSE.txt',
    description='Use git to sync a project directory on an OS X client with a'
                ' remote server.',
    long_description=open('README.txt').read(),
    classifiers=[
        'Intended Audience :: Developers',
        'Environment :: MacOS X',
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Topic :: Communications :: File Sharing',
        'Topic :: Utilities',
    ],
    install_requires=[
        "Fabric >= 1.8.0",
        "MacFSEvents >= 0.3",
        "PyYAML >= 3.10",
        "pync >= 1.4",
    ],
)
