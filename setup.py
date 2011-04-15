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
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##
##
"""Setup file for Stoq package"""

import fnmatch
import os
import platform
import sys

try:
    import py2exe
except ImportError:
    pass

#
# Dependency checking
#
KIWI_REQUIRED = (1, 9, 27)
STOQLIB_REQUIRED = (0, 9, 15)

# kiwi is only here because we need to use it in setup.py itself,
# the rest of the dependency checks should be done in stoqlib.
dependencies = [('kiwi', 'kiwi', KIWI_REQUIRED,
                 'http://www.async.com.br/projects/kiwi/',
                 lambda x: x.kiwi_version),
                ('Stoqlib', 'stoqlib', STOQLIB_REQUIRED,
                 'http://www.stoq.com.br',
                 lambda x: tuple([int(i)  for i in x.version.split('.')]))]

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
    'bin/stoqdbadmin',
    'bin/stoqruncmd',]
data_files = [
    ('$datadir/pixmaps',
     listfiles('data/pixmaps', '*.*')),
    ('$datadir/glade',
     listfiles('data', 'glade', '*.glade') +
     listfiles('data', 'glade', '*.ui')),
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
windows = []

def findmods(path, strip=''):
    r = []
    for root, dirnames, filenames in os.walk(path):
        for filename in fnmatch.filter(filenames, '*.py'):
             f = os.path.join(root, filename)
             f = f[len(strip):]
             if '__init__' in f:
                 continue
             if '#' in f:
                 continue
             f = f.replace('.py', '')
             f = f.replace(os.sep, '.')
             r.append(f)
    return r

options = {}

if platform.system() == "Windows":
    sys.path.insert(0, "../stoqlib/external")
    mods = (findmods('stoq') +
            findmods('../stoqlib/stoqlib', '../stoqlib/'))
    mods.append('reportlab.pdfbase._fontdata_enc_macexpert')
    mods.append('reportlab.pdfbase._fontdata_enc_macroman')
    mods.append('reportlab.pdfbase._fontdata_enc_pdfdoc')
    mods.append('reportlab.pdfbase._fontdata_enc_standard')
    mods.append('reportlab.pdfbase._fontdata_enc_symbol')
    mods.append('reportlab.pdfbase._fontdata_enc_winansi')
    mods.append('reportlab.pdfbase._fontdata_enc_zapfdingbats')
    mods.append('reportlab.pdfbase._fontdata_widths_courier')
    mods.append('reportlab.pdfbase._fontdata_widths_courierbold')
    mods.append('reportlab.pdfbase._fontdata_widths_courieroblique')
    mods.append('reportlab.pdfbase._fontdata_widths_courierboldoblique')
    mods.append('reportlab.pdfbase._fontdata_widths_helvetica')
    mods.append('reportlab.pdfbase._fontdata_widths_helveticabold')
    mods.append('reportlab.pdfbase._fontdata_widths_helveticaoblique')
    mods.append('reportlab.pdfbase._fontdata_widths_helveticaboldoblique')
    mods.append('reportlab.pdfbase._fontdata_widths_symbol')
    mods.append('reportlab.pdfbase._fontdata_widths_timesbold')
    mods.append('reportlab.pdfbase._fontdata_widths_timesbolditalic')
    mods.append('reportlab.pdfbase._fontdata_widths_timesitalic')
    mods.append('reportlab.pdfbase._fontdata_widths_timesroman')
    mods.append('reportlab.pdfbase._fontdata_widths_zapfdingbats')

    options['py2exe'] = {
        'packages': 'encodings',
        'includes': 'glib, gobject, gio, atk, cairo, pango, pangocairo, gtk, serial, formencode, sqlobject, _elementtree, xml.etree, ' + ','.join(mods) }
    windows.append({ 'script': 'stoqapp.py',
                     'icon_resources': [(0, 'data/pixmaps/stoq.ico')]})

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
      templates=templates,
      windows=windows,
      options=options)

