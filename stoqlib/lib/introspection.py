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

"""Introspection helpers for fetching classes, interfaces and adapters
"""

import glob
import inspect
import os

from kiwi.dist import listpackages
from kiwi.python import namedAny
from zope.interface import implementedBy
from zope.interface.interface import InterfaceClass

from stoqlib.domain.base import ModelAdapter, ORMObjectAdapter

from stoqlib.lib.component import Adapter


def get_all_classes(package):
    """
    Gets a generator with classes.
    @returns: a generator.
    """
    for package in listpackages(package):
        # stoqlib.domain -> stoqlib/domain
        package = package.replace('.', os.path.sep)

        # List all python files in stoqlib/domain
        for filename in glob.glob(os.path.join(package, '*.py')):
            # Avoid tests.
            if 'test/' in filename:
                continue

            # FIXME: Temporary fix until storm is installed properly
            #        in the buildbot environment
            if 'stormorm' in filename:
                continue

            # stoqlib/domain/base.py -> stoqlib.domain.base
            modulename = filename[:-3].replace(os.path.sep, '.')
            module = namedAny(modulename)
            for unused, klass in inspect.getmembers(module, inspect.isclass):
                yield klass


def get_interfaces_for_package(package):
    """
    Gets a generator with classes which implements at least one interface.
    @returns: a generator.
    """
    for klass in get_all_classes(package):
        if not implementedBy(klass):
            continue
        if not klass.__module__.startswith(package + '.'):
            continue
        if issubclass(klass, InterfaceClass):
            continue
        yield klass


def get_all_adapters():
    """
    Gets a generator with adapter classes.
    @returns: a generator.
    """
    for klass in get_all_classes('stoqlib'):
        if not issubclass(klass, Adapter):
            continue
        # Skip bases classes
        if klass in [Adapter, ORMObjectAdapter, ModelAdapter]:
            continue

        yield klass
