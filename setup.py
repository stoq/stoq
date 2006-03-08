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


from distutils.core import setup
from distutils.command.install_data import install_data

from kiwi.dist import (KiwiInstallData, KiwiInstallLib, compile_po_files,
                       listfiles, listpackages)

from stoq import __version__

PACKAGE = 'stoq'

class StoqInstallData(KiwiInstallData):
    def run(self):
        self.data_files.extend(compile_po_files(PACKAGE))
        install_data.run(self)

class StoqInstallLib(KiwiInstallLib):
    resources = dict(locale='$prefix/share/locale',
                     docs='$prefix/share/doc/stoq',
                     basedir='$prefix')
    global_resources = dict(pixmaps='$datadir/pixmaps',
                            glade='$datadir/glade',
                            config='$sysconfdir/stoq')

data_files = [
    ('$datadir/pixmaps',
     listfiles('data/pixmaps', '*.png')),
    ('$datadir/bin',  ['bin/init-database']),
    ('$datadir/glade',
     listfiles('data', '*.glade')),
    ('$sysconfdir',  ''),
    ('share/doc/stoq',
     ['AUTHORS', 'CONTRIBUTORS', 'COPYING', 'README', 'NEWS']),
    ]

setup(name=PACKAGE,
      version=__version__,
      author='Async Open Source',
      author_email='evandro@async.com.br',
      url='http://www.async.com.br/projects/stoq/wiki',
      license='GPL',
      packages=listpackages(PACKAGE),
      scripts=['bin/stoq'],
      data_files=data_files,
      cmdclass=dict(install_lib=StoqInstallLib,
                    install_data=StoqInstallData))

