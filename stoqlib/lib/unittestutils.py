# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2011 Async Open Source <http://www.async.com.br>
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
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

import os

from kiwi.python import ClassInittableObject

import stoqlib
from stoqlib.lib.osutils import list_recursively


def get_stoq_sources(root):
    for dirpath in ['stoq', 'stoqlib', 'plugins']:
        path = os.path.join(root, dirpath)
        for fname in list_recursively(path, '*.py'):
            if fname.endswith('__init__.py'):
                continue
            yield fname


class SourceTest(ClassInittableObject):
    @classmethod
    def __class_init__(cls, namespace):
        root = os.path.dirname(os.path.dirname(stoqlib.__file__)) + '/'
        cls.root = root
        for filename in get_stoq_sources(root):
            testname = filename[len(root):]
            if not cls.filename_filter(testname):
                continue
            testname = testname[:-3].replace('/', '_')
            name = 'test_%s' % (testname, )
            func = lambda self, r=root, f=filename: self.check_filename(r, f)
            func.__name__ = name
            setattr(cls, name, func)

    def check_filename(self, root, filename):
        pass

    @classmethod
    def filename_filter(cls, filename):
        if cls.__name__ == 'SourceTest':
            return False
        else:
            return True
