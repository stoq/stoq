#!/usr/bin/env python
#
# Copyright (C) 2005 Async Open Source
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.
#

from distutils.command.install_data import install_data
from distutils.core import setup

from kiwi.dist import TemplateInstallLib, compile_po_files, listfiles

from stoqlib.__version__ import version

PACKAGE = 'stoqlib'

class StoqLibInstallData(install_data):
    def run(self):
        self.data_files.extend(compile_po_files(PACKAGE))
        install_data.run(self)

class StoqLibInstallLib(TemplateInstallLib):
    name = PACKAGE
    resources = dict(locale='$prefix/share/locale')
    global_resources = dict(pixmaps='$datadir/pixmaps',
                            glade='$datadir/glade')
    
setup(name=PACKAGE,
      version='.'.join(map(str, version)),
      author="Async Open Source",
      author_email="evandro@async.com.br",
      url="http://www.async.com.br/projects/",
      license="GNU LGPL 2.1 (see COPYING)",
      data_files=[
        ('share/stoqlib/pixmaps',
         listfiles('stoqlib/gui/pixmaps', '*.xpm') +
         listfiles('stoqlib/gui/pixmaps', '*.png')),
        ('share/stoqlib/glade',
         listfiles('stoqlib/gui/glade', '*.glade')),
        ],
    packages=['stoqlib',
              'stoqlib.gui',
              'stoqlib.reporting'],
    cmdclass=dict(install_data=StoqLibInstallData,
                  install_lib=StoqLibInstallLib),
    )

