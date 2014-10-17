# -*- encoding: utf8 -*-
import glob
import io
import re
from os.path import basename
from os.path import dirname
from os.path import join
from os.path import splitext

from setuptools import find_packages
from setuptools import setup

def read(*names, **kwargs):
    return io.open(
        join(dirname(__file__), *names),
        encoding=kwargs.get("encoding", "utf8")
    ).read()

setup(
    name='GitSync',
    version="0.2",
    license='MIT',
    description='Use git to sync a project directory on an OS X client with a remote server.',
    long_description="%s\n%s" % (read("README.rst"), re.sub(":obj:`~?(.*?)`", r"``\1``", read("CHANGELOG.rst"))),
    author='Jachin Rupe',
    author_email='jachin@clockwork.net',
    url="https://github.com/clockwork/GitSync",
    packages=find_packages('src'),
    package_dir={'': 'src'},
    py_modules=[splitext(basename(i))[0] for i in glob.glob("src/*.py")],
    scripts=['bin/git_sync'],
    include_package_data=True,
    zip_safe=False,
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
        "GitSyncLib >= 0.1.3",
        "Fabric >= 1.8.0",
        "MacFSEvents >= 0.3",
        "PyYAML >= 3.10",
        "pync >= 1.6.1",
    ],
)
