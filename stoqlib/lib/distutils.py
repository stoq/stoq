# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013 Async Open Source
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

import fnmatch
import os

import stoqlib

source_root = os.path.abspath(os.path.join(
    os.path.dirname(stoqlib.__file__), '..'))


def get_all_source_files():
    """
    Fetches a list of all the source code files that are a part of Stoq.

    :returns: a list of filenames
    """
    for part in ['stoq', 'stoqlib', 'plugins']:
        path = os.path.join(source_root, part)
        for dirname, dirnames, filenames in os.walk(path):
            for filename in fnmatch.filter(filenames, '*.py'):
                if (filename.startswith('.#') or
                    filename.startswith('#')):
                    continue
                yield os.path.join(dirname, filename)
