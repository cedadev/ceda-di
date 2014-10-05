# BSD Licence
# Copyright (c) 2014, Science & Technology Facilities Council (STFC)
# All rights reserved.
#
# See the LICENSE file in the source distribution of this software for
# the full license text.

from setuptools import setup, find_packages
import sys, os


# Import version from the top-level package
sys.path[:0] = [os.path.join(os.path.dirname(__file__), 'src')]
from ceda_di import __version__
#from ceda_di import __doc__ as long_description

setup(name='ceda-di',
      version=__version__,
      description="A library interacting with ESGF services within Python",
      #long_description=long_description,
      classifiers=[
        'Development Status :: 3 - Alpha',
        'License :: OSI Approved :: BSD License',
        'Topic :: Scientific/Engineering',
        'Programming Language :: Python :: 2.7',
        ], # Get strings from http://pypi.python.org/pypi?%3Aaction=list_classifiers
      keywords='',
      author='Charles Newey',
      author_email='Charles.Newey@stfc.ac.uk',
      #url='http://github.com/cedadev/ceda-di',
      #download_url='',
      license='BSD',
      packages=find_packages('src', exclude=['ez_setup', 'examples', 'test']),
      package_dir={'': 'src'},
      include_package_data=True,
      zip_safe=False,
      
      #!TODO: Decide whether to use setuptools or requirements file for dependencies.
      
      # See pip_requirements.txt for dependencies
      #install_requires=[
      #],
      
      entry_points= {
        },
      #test_suite='nose.collector',
      )
