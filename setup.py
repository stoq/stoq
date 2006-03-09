#!/usr/bin/env python

# Setup file for StoqDrivers
# Code by Async Open Source <http://www.async.com.br>


#
# Dependency checking
#


dependencies = [('zope.interface', '3.0', None),
                ('kiwi', (1, 9, 6), lambda x: x.kiwi_version),
                ('serial', '2.1', None)]
for package_name, version, attr in dependencies:
    try:
        module = __import__(package_name, {}, {}, [])
        if attr:
            assert attr(module) >= version
    except (ImportError, AssertionError):
        raise SystemExit("Stoqdrivers requires %s version %s or higher"
                         % (package_name, version))


#
# Package installation
#


from distutils.core import setup

from kiwi.dist import listpackages, listfiles, KiwiInstallData, KiwiInstallLib

class StoqdriversInstallLib(KiwiInstallLib):
    global_resources = dict(conf="$datadir/conf")
    resources = dict(locale="$prefix/share/locale")

from stoqdrivers import __version__

setup(
    name = "stoqdrivers",
    version =  ".".join(map(str, __version__)),
    author="Async Open Source",
    author_email="stoq-devel@async.com.br",
    description = "Useful drivers for Stoq and retail systems",
    long_description="""
    This is a powerful collection of device drivers written in Python and
    totally focused on retail systems. Stoqdrivers also offers an
    unified API for devices like fiscal printers which makes it easy to
    embed in many applications.
    """,
    url = "http://www.stoq.com.br",
    license = "GNU LGPL 2.1 (see COPYING)",
    packages = listpackages('stoqdrivers'),
    data_files = [("$datadir/conf",
                   listfiles("stoqdrivers/conf", "*.ini"))],
    cmdclass=dict(install_lib=StoqdriversInstallLib,
                  install_data=KiwiInstallData),
    )
