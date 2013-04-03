# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
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
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##

import glob
import os
import StringIO
import unittest
from xml.etree import ElementTree

from docutils.core import publish_doctree

import stoq


class TestAPIDoc(unittest.TestCase):
    def setUp(self):
        self.errors = []

    def test_apidoc(self):
        for rst_name in glob.glob('docs/api/*.rst'):
            self.check_filename(rst_name)

        if self.errors:
            self.fail('ERROR: ' + '\n'.join(sorted(self.errors)))

    def _list_modules(self, rst_filename):
        path = os.path.basename(rst_filename)[:-4].replace('.', '/')
        dir_name = os.path.abspath(
            os.path.join(
                os.path.dirname(stoq.__file__), '..', path))

        py_files = glob.glob('%s/*.py' % (dir_name, ))
        modules = [os.path.basename(f)[:-3] for f in py_files]

        # stoqlib.domain is special cases as we merged the payment module
        # into one documentation file.
        if path == 'stoqlib/domain':
            modules.extend('payment.%s' % (os.path.basename(f)[:-3], )
                           for f in glob.glob('stoqlib/domain/payment/*.py'))
            modules.remove('payment.__init__')

        try:
            modules.remove('__init__')
        except ValueError:
            pass

        return modules

    def check_filename(self, rst_filename):
        # Skip l10n modules that needs to be cleaned up
        if os.path.basename(rst_filename) in [
            'stoqlib.l10n.generic.rst',
            'stoqlib.l10n.br.rst',
            'stoqlib.l10n.sv.rst']:
            return

        # List all modules
        modules = self._list_modules(rst_filename)

        # Parse RST
        rst_data = open(rst_filename).read()
        doc = publish_doctree(
            rst_data,
            settings_overrides={
                'input_encoding': 'utf-8',
                'warning_stream': StringIO.StringIO()})

        # Convert to an XML string
        xml = doc.asdom().toxml()

        # Parse with ElementTree
        doctree = ElementTree.fromstring(xml)
        for section in doctree.findall('section'):
            name = section.attrib.get('names')
            if not name.startswith(':mod:'):
                continue
            if name.endswith(' package'):
                continue
            if name == 'subpackage':
                continue

            # Check for removed python modules
            module_name = name[5:].split('`')[1]
            try:
                modules.remove(module_name)
            except ValueError:
                self.errors.append('%s: %s module does not exist' % (
                    rst_filename, module_name))

        # Check for missing python modules
        for module in modules:
            # Skip test modules
            if module.startswith('test_'):
                continue
            # Skip a couple of external modules
            if module in [
                'generictreemodel',
                'gicompat']:
                continue
            self.errors.append('%s: %s module is missing' % (
                rst_filename, module))

if __name__ == '__main__':
    unittest.main()
