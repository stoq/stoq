# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2011 Async Open Source
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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

#
# Dependency checking
#

from stoq.lib.dependencies import DependencyChecker
dc = DependencyChecker()
dc.text_mode = True
# We don't need latest kiwi in here
dc.check_kiwi([1, 9, 26])

#
# Package installation
#

import os
import sys

from kiwi.dist import setup, listfiles, listpackages

from stoq import website, version


building_egg = 'bdist_egg' in sys.argv
if building_egg:
    plugin_base_dir = os.path.join('stoq', 'data')
else:
    plugin_base_dir = '$datadir'

plugin_dir = os.path.join(plugin_base_dir, 'plugins')


def listplugins(plugins, exts):
    dirs = []
    for package in listpackages('plugins'):
        # strip plugins
        dirs.append(package.replace('.', '/'))
    files = []
    for directory in dirs:
        install_dir = os.path.join(plugin_base_dir, directory)
        files.append((install_dir, listfiles(directory, '*.py')))
        files.append((install_dir, listfiles(directory, '*.plugin')))

    for plugin in plugins:
        for kind, suffix in exts:
            x = listfiles('plugins', plugin, kind, suffix)
            if x:
                path = os.path.join(plugin_dir, '%s', '%s')
                files.append((path % (plugin, kind), x))

        files.append((os.path.join(plugin_dir, plugin),
                      listfiles('plugins', plugin, '*.py')))

    return files


def list_templates():
    files = []
    dir_prefix = '$datadir/'
    for root, _, _ in os.walk('data/template'):
        parts = root.split(os.sep)
        files.append((dir_prefix + os.sep.join(parts[1:]),
                     listfiles(*(parts + ['*html']))))
        files.append((dir_prefix + os.sep.join(parts[1:]),
                     listfiles(*(parts + ['*css']))))
    return files

packages = listpackages('stoq')
packages.extend(listpackages('stoqlib', exclude='stoqlib.tests'))

scripts = [
    'bin/stoq',
    'bin/stoqdbadmin',

    # FIXME: move these to /usr/lib/stoq/
    'bin/stoqcreatedbuser',
    'bin/stoq-daemon',
]
data_files = [
    ('$datadir/csv', listfiles('data', 'csv', '*.csv')),
    ('$datadir/glade', listfiles('data', 'glade', '*.ui')),
    ('$datadir/misc', listfiles('data/misc', '*.*')),
    ('$datadir/pixmaps', listfiles('data', 'pixmaps', '*.png')),
    ('$datadir/pixmaps', listfiles('data', 'pixmaps', '*.svg')),
    ('$datadir/pixmaps', listfiles('data', 'pixmaps', '*.jpg')),
    ('$datadir/pixmaps', listfiles('data', 'pixmaps', '*.gif')),
    ('$datadir/pixmaps', listfiles('data', 'pixmaps', '*.bmp')),
    ('$datadir/sql', listfiles('data', 'sql', '*.sql')),
    ('$datadir/sql', listfiles('data', 'sql', '*.py')),
    ('$datadir/uixml', listfiles('data', 'uixml', '*.xml')),
    ('$datadir/html', listfiles('data', 'html', '*.html')),
    ('$datadir/html/css', listfiles('data', 'html', 'css', '*.css')),
    ('$datadir/html/images', listfiles('data', 'html', 'images', '*.png')),
    ('$datadir/html/js', listfiles('data', 'html', 'js', '*.js')),
]

data_files += list_templates()

if building_egg:
    data_files.append(
        ('stoq/data/docs',
         ['AUTHORS', 'CONTRIBUTORS', 'COPYING', 'COPYING.pt_BR',
          'COPYING.stoqlib', 'README', 'docs/copyright']))
else:
    data_files.extend([
        ('share/applications', ['stoq.desktop']),
        ('share/doc/stoq',
         ['AUTHORS', 'CONTRIBUTORS', 'COPYING', 'COPYING.pt_BR',
          'COPYING.stoqlib', 'README', 'docs/copyright']),
        ('share/gnome/help/stoq/C',
         listfiles('docs/manual/pt_BR', '*.page')),
        ('share/gnome/help/stoq/C',
         listfiles('docs/manual/pt_BR', '*.xml')),
        ('share/gnome/help/stoq/C/figures',
         listfiles('docs/manual/pt_BR/figures', '*.png')),
        ('share/gnome/help/stoq/C/figures',
         listfiles('docs/manual/pt_BR/figures', '*.svg')),
        ('share/icons/hicolor/48x48/apps', ['data/pixmaps/stoq.png']),
        ('share/polkit-1/actions', ['data/br.com.stoq.createdatabase.policy']),
    ])

# FIXME: We are using $datadir/../ for locale/doc as a workaround for kiwi.
# Without this, he would not find the proper resource when installing
# stoq from a wheel
resources = dict(
    locale='$datadir/../locale',
    plugin=plugin_dir,
)
global_resources = dict(
    csv='$datadir/csv',
    docs='$datadir/../doc/stoq',
    glade='$datadir/glade',
    uixml='$datadir/uixml',
    html='$datadir/html',
    misc='$datadir/misc',
    pixmaps='$datadir/pixmaps',
    sql='$datadir/sql',
    template='$datadir/template',
)

PLUGINS = ['ecf', 'nfe', 'books', 'optical']
PLUGIN_EXTS = [('csv', '*csv'),
               ('glade', '*.ui'),
               ('sql', '*.sql'),
               ('sql', '*.py')]

data_files += listplugins(PLUGINS, PLUGIN_EXTS)

# TODO: Put additional requirements that are not on pypi here. See:
# https://pythonhosted.org/setuptools/setuptools.html#dependencies-that-aren-t-in-pypi
# Try to make a way to integrate it with debian packaging, just like the
# dependencies bellow.
install_requires = [
    "Mako >= 0.2.5",
    "PIL >= 1.1.5",
    "PyGTK >= 2.20",
    "Twisted >= 0.2.5",
    "aptdaemon >= 3.0",
    "dateutil >= 1.4.1",
    "kiwi-gtk >= 1.9.29",
    "psycopg2 >= 2.0.5",
    "pypoppler >= 0.12.1",
    "reportlab >= 2.4",
    "stoqdrivers >= 0.9.21",
    "storm >= 0.19",
    "weasyprint >= 0.15",
    "xlwt >= 0.7.2",
    "zope.interface >= 3.0",
]

setup(name='stoq',
      version=version,
      author="Async Open Source",
      author_email="stoq-devel@async.com.br",
      description="A powerful retail system",
      long_description="""
      Stoq is an advanced retails system which has as main goals the
      usability, good devices support, and useful features for retails.
      """,
      url=website,
      license="GNU GPL 2.0 and GNU LGPL 2.1 (see COPYING and COPYING.stoqlib)",
      packages=packages,
      data_files=data_files,
      scripts=scripts,
      resources=resources,
      install_requires=install_requires,
      global_resources=global_resources,
      zip_safe=building_egg)
