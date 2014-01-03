from distutils.core import setup

setup(
    name='GitSync',
    version='0.1.0',
    author='Jachin Rupe',
    author_email='jachin@clockwork.net',
    packages=['gitsync'],
    scripts=['bin/git_sync'],
    url='http://pypi.python.org/pypi/GitSync/',
    license='LICENSE.txt',
    description='Use git to sync a project directory on an OS X client with a'
                ' remote server.',
    long_description=open('README.txt').read(),
    install_requires=[
        "Fabric >= 1.8.0",
        "MacFSEvents >= 0.3",
        "PyYAML >= 3.10",
    ],
)
