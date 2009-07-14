# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2009 Async Open Source
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

#
# Dependency checking
#


PSYCOPG_REQUIRED = [2, 0, 5]
KIWI_REQUIRED = (1, 9, 25)
STOQDRIVERS_REQUIRED = (0, 9, 7)

def psycopg_check(mod):
    version = mod.__version__.split(' ', 1)[0]
    return map(int, version.split('.'))

dependencies = [('ZopeInterface', 'zope.interface', '3.0',
                 'http://www.zope.org/Products/ZopeInterface',
                 None),
                ('kiwi', 'kiwi', KIWI_REQUIRED,
                 'http://www.async.com.br/projects/kiwi/',
                 lambda x: x.kiwi_version),
                ('Gazpacho', 'gazpacho', '0.6.6',
                 'http://gazpacho.sicem.biz',
                 lambda x: x.__version__),
                ('Psycopg', 'psycopg2', PSYCOPG_REQUIRED,
                 'http://www.initd.org/projects/psycopg2',
                 psycopg_check),
                ('Stoqdrivers', 'stoqdrivers', STOQDRIVERS_REQUIRED,
                 'http://www.stoq.com.br',
                 lambda x: x.__version__),
                ('Python Imaging Library (PIL)', 'PIL', '1.1.5',
                 'http://www.pythonware.com/products/pil/', None),
                ('Reportlab', 'reportlab', '1.20',
                 'http://www.reportlab.org/', lambda x: x.Version),
                ('python-dateutil', 'dateutil', '1.3',
                 'http://labix.org/python-dateutil', lambda x: x.__version__)]

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
            raise SystemExit(
                "The '%s' module was found but it is too new for stoqlib.\n "
                "requirements. Please install at least version %s of %s. "
                "Visit %s." % (
                module_name, required_version, package_name, url))

    elif required_version > installed_version:
        raise SystemExit(
            "The '%s' module was found but it was not recent enough.\n"
            "Please install at least version %s of %s. Visit %s."
            % (module_name, required_version, package_name, url))


#
# Package installation
#

from kiwi.dist import setup, listfiles, listpackages

from stoqlib import version, website

def listexternal():
    dirs = []
    for package in listpackages('external'):
        # strip external
        dirs.append(package.replace('.', '/'))
    files = []
    for directory in dirs:
        files.append(('lib/stoqlib/' + directory[9:],
                      listfiles(directory, '*.py')))
    return files

def listplugins():
    dirs = []
    for package in listpackages('plugins'):
        # strip plugins
        dirs.append(package.replace('.', '/'))
    files = []
    for directory in dirs:
        install_dir = 'lib/stoqlib/%s' % directory
        files.append((install_dir, listfiles(directory, '*.py')))
        files.append((install_dir, listfiles(directory, '*.plugin')))
    return files

data_files = [
    ('$datadir/pixmaps', listfiles('data', 'pixmaps', '*.png')),
    ('$datadir/sql', listfiles('data', 'sql', '*.sql')),
    ('$datadir/sql', listfiles('data', 'sql', '*.py')),
    ('$datadir/glade', listfiles('data', 'glade', '*.glade')),
    ('$datadir/fonts', listfiles('data', 'fonts', '*.ttf')),
    ('$datadir/csv', listfiles('data', 'csv', '*.csv')),
    ('$datadir/template', listfiles('data', 'template', '*.rml')),
    ('share/doc/stoqlib',
     ('AUTHORS', 'CONTRIBUTORS', 'README'))]
data_files += listexternal()
resources = dict(
    locale='$prefix/share/locale',
    plugin='$prefix/lib/stoqlib/plugins',
    )
global_resources = dict(
    pixmaps='$datadir/pixmaps',
    sql='$datadir/sql',
    glade='$datadir/glade',
    fonts='$datadir/fonts',
    csv='$datadir/csv',
    template='$datadir/template',
    )

# ECFPlugin
data_files += listplugins()
data_files += [
    ('$prefix/lib/stoqlib/plugins/ecf/glade',
     listfiles('plugins', 'ecf', 'glade', '*.glade')),
    ('$prefix/lib/stoqlib/plugins/ecf/sql',
     listfiles('plugins', 'ecf', 'sql', '*.sql')),
    ]

setup(name='stoqlib',
      version=version,
      author="Async Open Source",
      author_email="stoq-devel@async.com.br",
      description="A powerful retail system library",
      long_description="""
      Stoqlib offers infrastructure used by Stoq.
      Database schema & importing, domain classes with business logic,
      dialogs, editors and search infrastructure, report generation,
      plugins, testsuites and API documentation.
      """,
      url=website,
      license="GNU LGPL 2.1 (see COPYING)",
      packages=listpackages('stoqlib', exclude='stoqlib.tests'),
      data_files=data_files,
      resources=resources,
      global_resources=global_resources,
      )
