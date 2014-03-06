from distutils.core import setup

setup(
    name='GitSync',
    version='0.1.1',
    author='Jachin Rupe',
    author_email='jachin@clockwork.net',
    packages=['gitsync'],
    scripts=['bin/git_sync'],
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
