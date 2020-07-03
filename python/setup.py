# BSD Licence
# Copyright (c) 2014, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

from setuptools import find_packages
from setuptools import setup
import os
import sys

# Import version from the top-level package
sys.path.insert(1, os.path.join(os.path.dirname(__file__), 'src'))
from ceda_di import __version__
from ceda_di import __doc__ as long_description

setup(
    name='ceda-di',
    version=__version__,
    description='',
    long_description=long_description,
    # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: BSD License',
        'Topic :: Scientific/Engineering',
        'Programming Language :: Python :: 2.7',
    ],
    keywords='',
    author='Charles Newey',
    author_email='Charles.Newey@stfc.ac.uk',
    url='http://github.com/cedadev/ceda-di',
    download_url='http://github.com/cedadev/ceda-di',
    license='BSD',
    packages=find_packages('src', exclude=['ez_setup', 'examples', 'test']),
    package_dir={'': 'src'},
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'certifi',
        'cftime',
        'docopt',
        'elasticsearch',
        'ExifRead',
        'netCDF4',
        'numpy',
        'pyhdf',
        'python-dateutil',
        'six',
        'urllib3',
        'xmltodict'
    ],
    extras_require={
        'test': ['mock']
    },
    entry_points={
        'console_scripts': [
            'ceda-di = ceda_di.main:main',
        ],
    },
)
