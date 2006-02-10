# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005, 2006 Async Open Source
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU Lesser General Public License
## as published by the Free Software Foundation; either version 2
## of the License, or (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
##
##
## Author(s):       Evandro Vale Miquelito      <evandro@async.com.br>
##                  Johan Dahlin                <jdahlin@async.com.br>
##
"""Setup file for stoqlib package"""


from distutils.command.install_data import install_data
from distutils.core import setup

from kiwi.dist import (TemplateInstallLib, compile_po_files, listfiles,
                       listpackages)

from stoqlib import __version__, __program_name__, __website__


class StoqLibInstallData(install_data):
    def run(self):
        self.data_files.extend(compile_po_files('stoqlib'))
        install_data.run(self)

class StoqLibInstallLib(TemplateInstallLib):
    name = __program_name__
    resources = dict(locale='$prefix/share/locale')
    global_resources = dict(pixmaps='$datadir/pixmaps',
                            sql='$datadir/sql',
                            glade='$datadir/glade',
                            fonts='$datadir/fonts')

setup(name=__program_name__,
      version=__version__,
      author="Async Open Source",
      author_email="evandro@async.com.br",
      url=__website__,
      license="GNU LGPL 2.1 (see COPYING)",
      data_files=[
        ('share/stoqlib/pixmaps',
         listfiles('data/pixmaps', '*.png')),
        ('share/stoqlib/sql',
         listfiles('data/sql', '*.sql')),
        ('share/stoqlib/glade',
         listfiles('data', '*.glade')),
        ('share/doc/stoqlib',
         ('AUTHORS', 'CONTRIBUTORS', 'NEWS', 'README')),
        ],
    packages=listpackages('stoqlib'),
    cmdclass=dict(install_data=StoqLibInstallData,
                  install_lib=StoqLibInstallLib),
    )

