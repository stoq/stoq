# -*- coding: utf-8 -*-
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


#
# Dependencies check
#


dependencies = [('zope.interface', '3.0', None),
                ('kiwi', (1, 9, 6), lambda x: x.__version__.version),
                ('gazpacho', '0.6.5', lambda x: x.__version__),
                ('psycopg', '1.1.18', lambda x: x.__version__),
                ('sqlobject', '0.7.0', None),
                ('stoqdrivers', (0,3), lambda x: x.__version__),
                ('PIL', '1.1.5', None),
                ('reportlab', '1.20', lambda x: x.Version)]

for package_name, version, attr in dependencies:
    try:
        module = __import__(package_name, {}, {}, [])
        if attr:
            assert attr(module) >= version
    except ImportError, AssertionError:
        raise SystemExit("Stoqlib requires %s %s or higher"
                         % (package_name, version))


#
# Package installation
#


from distutils.core import setup
from distutils.command.install_data import install_data

from kiwi.dist import (KiwiInstallData, KiwiInstallLib, compile_po_files,
                       listfiles, listpackages)

from stoqlib import version, website

class StoqLibInstallData(KiwiInstallData):
    def run(self):
        self.data_files.extend(compile_po_files('stoqlib'))
        install_data.run(self)

class StoqLibInstallLib(KiwiInstallLib):
    resources = dict(locale='$prefix/share/locale')
    global_resources = dict(pixmaps='$datadir/pixmaps',
                            sql='$datadir/sql',
                            glade='$datadir/glade',
                            fonts='$datadir/fonts')

setup(name='stoqlib',
      version=version,
      author="Async Open Source",
      author_email="stoq-devel@async.com.br",
      description="A powerful retail system library",
      long_description="""
      This library offers many special tools for retail system applications
      such reports infrastructure, basic dialogs and searchbars and domain data in a
      persistent level.""",
      url=website,
      license="GNU LGPL 2.1 (see COPYING)",
      data_files=[
        ('$datadir/pixmaps',
         listfiles('data/pixmaps', '*.png')),
        ('$datadir/sql',
         listfiles('data/sql', '*.sql')),
        ('$datadir/glade',
         listfiles('data', '*.glade')),
        ('$datadir/fonts',
         listfiles('data', 'fonts', '*.ttf')),
        ('share/doc/stoqlib',
         ('AUTHORS', 'CONTRIBUTORS', 'README')),
        ],
    packages=listpackages('stoqlib', exclude='stoqlib.tests'),
    cmdclass=dict(install_data=StoqLibInstallData,
                  install_lib=StoqLibInstallLib),
    )

