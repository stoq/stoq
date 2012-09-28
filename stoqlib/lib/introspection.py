# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006 Async Open Source <http://www.async.com.br>
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

"""Introspection helpers for fetching classes and interfaces
"""

import glob
import inspect
import os

from kiwi.dist import listpackages
from kiwi.python import namedAny
from zope.interface import implementedBy
from zope.interface.interface import InterfaceClass

import stoqlib


def get_all_classes(root):
    """
    Gets a generator with classes.
    :returns: a generator.
    """
    # Convert to absolute path so it works within documentation tools
    basedir = os.path.dirname(stoqlib.__path__[0])
    root = os.path.join(basedir, root)
    for package in listpackages(root):
        # Remove absolute path
        package = package[len(basedir):]
        if package.startswith('.'):
            package = package[1:]
        # stoqlib.domain -> stoqlib/domain
        package = package.replace('.', os.path.sep)

        # List all python files in stoqlib/domain
        for filename in glob.glob(os.path.join(package, '*.py')):
            # Avoid tests.
            if 'test/' in filename:
                continue

            # stoqlib/domain/base.py -> stoqlib.domain.base
            modulename = filename[:-3].replace(os.path.sep, '.')
            module = namedAny(modulename)
            for unused, klass in inspect.getmembers(module, inspect.isclass):
                yield klass


def get_interfaces_for_package(package):
    """
    Gets a generator with classes which implements at least one interface.
    :returns: a generator.
    """
    for klass in get_all_classes(package):
        if not implementedBy(klass):
            continue
        if not klass.__module__.startswith(package + '.'):
            continue
        if issubclass(klass, InterfaceClass):
            continue
        yield klass
