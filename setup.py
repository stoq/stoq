#!/usr/bin/env python

# Setup file for StoqDrivers
# Code by Async Open Source <http://www.async.com.br>

from distutils.core import setup

from kiwi.dist import listpackages, listfiles, TemplateInstallLib

class StoqdriversInstallLib(TemplateInstallLib):
    name = "stoqdrivers"
    global_resources = dict(conf="$datadir/conf")

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
    packages = listpackages('stoqdrivers'),
    data_files = [("share/stoqdrivers/conf",
                   listfiles("stoqdrivers/conf", "*.ini"))],
    cmdclass=dict(install_lib=StoqdriversInstallLib),
    )
