#!/usr/bin/env python

# Setup file for StoqDrivers
# Code by Async Open Source <http://www.async.com.br>

from distutils.core import setup
from fnmatch import fnmatch
import os

def listfiles(*dirs):
    dir, pattern = os.path.split(os.path.join(*dirs))
    return [os.path.join(dir, filename)
            for filename in os.listdir(os.path.abspath(dir))
                if filename[0] != '.' and fnmatch(filename, pattern)]

version = ''
execfile("stoqdrivers/__version__.py")
assert version

setup(
    name = "Stoqdrivers",
    version =  ".".join(map(str, version)),
    description = "Useful drivers for Stoq and retail systems",
    long_description = """ """,

    author = "Async Open Source",
    author_email = "kiko@async.com.br",
    url = "http://www.async.com.br/projects/",
    license = "GNU LGPL 2.1 (see COPYING)",
    packages = ['stoqdrivers',
                'stoqdrivers.drivers',
                'stoqdrivers.drivers.daruma',
                'stoqdrivers.drivers.sweda',
                'stoqdrivers.drivers.bematech'],
    )
