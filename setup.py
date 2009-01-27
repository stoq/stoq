# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2009 Async Open Source <http://www.async.com.br>
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
## Foundation, Inc., or visit: http://www.gnu.org/.
##
##  Author(s):  Evandro Vale Miquelito      <evandro@async.com.br>
##              Johan Dahlin                <jdahlin@async.com.br>
##
##
"""Setup file for Stoq package"""

import sys

#
# Dependency checking
#
KIWI_REQUIRED = (1, 9, 23)
STOQLIB_REQUIRED = '0.9.7'

# kiwi is only here because we need to use it in setup.py itself,
# the rest of the dependency checks should be done in stoqlib.
dependencies = [('kiwi', 'kiwi', KIWI_REQUIRED,
                 'http://www.async.com.br/projects/kiwi/',
                 lambda x: x.kiwi_version),
                ('Stoqlib', 'stoqlib', STOQLIB_REQUIRED,
                 'http://www.stoq.com.br', lambda x: x.version)]

if ('build' in sys.argv or
    'install' in sys.argv):
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

from kiwi.dist import setup, listfiles, listpackages

from stoq import version

scripts = [
    'bin/stoq',
    'bin/stoqdbadmin']
data_files = [
    ('$datadir/pixmaps',
     listfiles('data/pixmaps', '*.*')),
    ('$datadir/glade',
     listfiles('data', 'glade', '*.glade')),
    ('$sysconfdir/stoq',  ''),
    ('share/doc/stoq',
     ['AUTHORS', 'CONTRIBUTORS', 'COPYING', 'README', 'NEWS'])]
resources = dict(
    locale='$prefix/share/locale',
    basedir='$prefix')
global_resources = dict(
    pixmaps='$datadir/pixmaps',
    glade='$datadir/glade',
    docs='$prefix/share/doc/stoq',
    config='$sysconfdir/stoq')

templates = [
    ('share/applications', ['stoq.desktop'])]

setup(name='stoq',
      version=version,
      author='Async Open Source',
      author_email='stoq-devel@async.com.br',
      description="An advanced retail system",
      long_description="""
      Stoq is an advanced retails system which has as main goals the
      usability, good devices support, and useful features for retails.
      """,
      url='http://www.stoq.com.br',
      license='GNU GPL (see COPYING)',
      packages=listpackages('stoq'),
      scripts=scripts,
      data_files=data_files,
      resources=resources,
      global_resources=global_resources,
      templates=templates)

