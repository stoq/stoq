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
## Foundation, Inc., or visit: http://www.gnu.org/.
##
##
## Author(s):       Evandro Vale Miquelito      <evandro@async.com.br>
##                  Johan Dahlin                <jdahlin@async.com.br>
##
"""Setup file for stoqlib package"""



#
# Dependency checking
#


dependencies = [('ZopeInterface', 'zope.interface', '3.0',
                 'http://www.zope.org/Products/ZopeInterface',
                 None),
                ('kiwi', 'kiwi', (1, 9, 9),
                 'http://www.async.com.br/projects/kiwi/',
                 lambda x: x.kiwi_version),
                ('Gazpacho', 'gazpacho', '0.6.6',
                 'http://www.gazpacho.sicem.biz',
                 lambda x: x.__version__),
                ('Psycopg', 'psycopg', '1.1.21',
                 'http://www.initd.org/projects/psycopg1',
                 (lambda x: x.__version__
                            and x.__version__ >= '1.1.21'
                            and x.__version__ < '2.0' or False)),
                ('SQLObject', 'sqlobject', '0.8.1',
                 'http://www.sqlobject.org', None),
                ('Stoqdrivers', 'stoqdrivers', (0, 4),
                 'http://www.stoq.com.br',
                 lambda x: x.__version__),
                ('Python Imaging Library (PIL)', 'PIL', '1.1.5',
                 'http://www.pythonware.com/products/pil/', None),
                ('Reportlab', 'reportlab', '1.20',
                 'http://www.reportlab.org/', lambda x: x.Version)]

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

    installed_version = get_version(module)
    if isinstance(installed_version, bool):
            if not installed_version:
                raise SystemExit("The '%s' module was found but it is too "
                                 "new for stoqlib requirements.\nPlease "
                                 "install at least version %s of %s. "
                                 "Visit %s." % (module_name,
                                                required_version,
                                                package_name, url))

    elif required_version > installed_version:
        raise SystemExit("The '%s' module was found but it was not "
                         "recent enough\nPlease install at least "
                         "version %s of %s. Visit %s."
                         % (module_name, required_version, package_name,
                            url))


#
# Package installation
#

from kiwi.dist import setup, listfiles, listpackages

from stoqlib import version, website

data_files = [
    ('$datadir/pixmaps', listfiles('data', 'pixmaps', '*.png')),
    ('$datadir/sql', listfiles('data', 'sql', '*.sql')),
    ('$datadir/glade', listfiles('data', 'glade', '*.glade')),
    ('$datadir/fonts', listfiles('data', 'fonts', '*.ttf')),
    ('share/doc/stoqlib',
     ('AUTHORS', 'CONTRIBUTORS', 'README'))]
resources = dict(
    locale='$prefix/share/locale')
global_resources = dict(
    pixmaps='$datadir/pixmaps',
    sql='$datadir/sql',
    glade='$datadir/glade',
    fonts='$datadir/fonts')

setup(name='stoqlib',
      version=version,
      author="Async Open Source",
      author_email="stoq-devel@async.com.br",
      description="A powerful retail system library",
      long_description="""
      Stoqlib offers many special tools for retail system applications
      such reports infrastructure, basic dialogs and searchbars and
      domain data in a persistent level.
      """,
      url=website,
      license="GNU LGPL 2.1 (see COPYING)",
      packages=listpackages('stoqlib', exclude='stoqlib.tests'),
      data_files=data_files,
      resources=resources,
      global_resources=global_resources,
      )

