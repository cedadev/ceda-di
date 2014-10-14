# Guide to This Directory

* "docs" - Sphinx documentation for Python project
* "src" - Python source code, with Sphinx comments and sample configuration file(s)
* "pip_requirements.txt" - Package list for ```pip``` installations (essentially what I use in my virtualenv)
    * Install with ```pip install -r pip_requirements.txt```

## Installing from ```pip_requirements.txt```

In theory, it should be straightforward to install all of the project's dependencies from the requirements file,
but unfortunately it isn't. Some of the Python packages depend on C or C++ packages that must be installed beforehand,
so I've tried to document here which packages are the "fussy" ones.

### PyHDF
The FTP mirror on PIP for the PyHDF library doesn't work at the time of writing (15th Sep 2014).

These commands should allow PyHDF to be installed (replace the URL with the most up-to-date version!)
```
export url="http://sourceforge.net/projects/pysclint/files/pyhdf/0.8.3/pyhdf-0.8.3.tar.gz/download"

#### IMPORTANT - set these before installing
export INCLUDE_DIRS="/usr/include/hdf" # <-- Change this to your 'hdf' C/C++ library include location (find / -name "hdf.h")
export LIBRARY_DIRS="/usr/lib" # <-- Change this to your 'hdf' C/C++ library shared object location (find / -name "libmfhdf.so")
export NOSZIP=1

wget -O pyhdf-0.8.3.tar.gz $url
pip install pyhdf --no-index --find-links ./
rm pyhdf-0.8.3
```

### PyHull
PyHull requires a very recent version of "setuptools". (5.7+)
By default, the version that ships with Python 2.7 is 2.2.

Luckily, this is easy to resolve:

```
pip install --upgrade setuptools
```
