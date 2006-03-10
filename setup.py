# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005, 2006 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
##  Author(s):  Evandro Vale Miquelito      <evandro@async.com.br>
##              Johan Dahlin                <jdahlin@async.com.br>
##
##
"""Setup file for Stoq package"""

#
# Dependency checking
#

dependencies = [('kiwi', 'kiwi', (1, 9, 6),
                 'http://www.async.com.br/projects/kiwi/',
                 lambda x: x.kiwi_version),
                ('Stoqlib', 'stoqlib', '0.7.0',
                 'http://www.stoq.com.br', lambda x: x.version)]

for (package_name, module_name, required_version, url,
     get_version) in dependencies:
    try:
        module = __import__(module_name, {}, {}, [])
    except ImportError:
        raise SystemExit("The '%s' module could not be found\n"
                         "Please install %s which can be found at %s"
                         % (module_name, package_name, url))

    if not get_version:
        continue

    if required_version > get_version(module):
        raise SystemExit("The '%s' module was found but it was not "
                         "recent enough\nPlease install at least "
                         "version %s of %s. Visit %s."
                         % (module_name, required_version, package_name,
                            url))


#
# Package installation
#


from distutils.core import setup
from distutils.command.install_data import install_data

from kiwi.dist import (KiwiInstallData, KiwiInstallLib, compile_po_files,
                       listfiles, listpackages)

from stoq import version

PACKAGE = 'stoq'

class StoqInstallData(KiwiInstallData):
    def run(self):
        self.data_files.extend(compile_po_files(PACKAGE))
        KiwiInstallData.run(self)

class StoqInstallLib(KiwiInstallLib):
    resources = dict(locale='$prefix/share/locale',
                     basedir='$prefix')
    global_resources = dict(pixmaps='$datadir/pixmaps',
                            glade='$datadir/glade',
                            docs='$prefix/share/doc/stoq',
                            config='$sysconfdir/stoq')

data_files = [
    ('$datadir/pixmaps',
     listfiles('data/pixmaps', '*.png')),
    ('$datadir/glade',
     listfiles('data', '*.glade')),
    ('$sysconfdir/stoq',  ''),
    ('share/doc/stoq',
     ['AUTHORS', 'CONTRIBUTORS', 'COPYING', 'README', 'NEWS']),
    ]

setup(name=PACKAGE,
      version=version,
      author='Async Open Source',
      author_email='stoq-devel@async.com.br',
      description="An advanced retail system",
      long_description="""
      This is an advanced retails system which has as main goals the
      usability, good devices support, and useful features for retails.
      """,
      url='http://www.stoq.com.br',
      license='GNU GPL (see COPYING)',
      packages=listpackages(PACKAGE),
      scripts=['bin/stoq', 'bin/init-database'],
      data_files=data_files,
      cmdclass=dict(install_lib=StoqInstallLib,
                    install_data=StoqInstallData))

