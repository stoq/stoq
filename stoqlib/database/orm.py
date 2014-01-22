# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (c) 2006, 2007 Canonical
## Copyright (C) 2008-2013 Async Open Source <http://www.async.com.br>
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
##            Gustavo Niemeyer <gustavo@niemeyer.net>
##

# This file is full of hacks to mimic the SQLObject API
# TODO:
# - Replace get/etc with storm.find()

"""Simple ORM abstraction layer"""

import warnings

from storm.base import Storm
from storm.store import Store

from stoqlib.database.exceptions import ORMObjectNotFound


class SQLObjectBase(Storm):
    """The root class of all SQLObject-emulating classes in your application.

    The general strategy for using Storm's SQLObject emulation layer
    is to create an application-specific subclass of SQLObjectBase
    (probably named "SQLObject") that provides an implementation of
    get_store to return an instance of :class:`storm.store.Store`. It may
    even be implemented as returning a global :class:`Store` instance. Then
    all database classes should subclass that class.
    """

    # FIXME: Remove
    @classmethod
    def get(cls, obj_id, store=None):
        warnings.warn("use store.get() or store.fetch()", DeprecationWarning,
                      stacklevel=2)
        obj = store.get(cls, obj_id)
        if obj is None:
            raise ORMObjectNotFound("Object not found")
        return obj

    # FIXME: Remove
    def sync(self):
        warnings.warn("use store.flush()", DeprecationWarning, stacklevel=2)
        store = self.store
        store.flush()
        store.autoreload(self)

    # FIXME: Remove
    @classmethod
    def delete(cls, id, store=None):
        warnings.warn("use store.remove()", DeprecationWarning, stacklevel=2)
        obj = store.get(cls, id)
        Store.of(obj).remove(obj)


class ORMObject(SQLObjectBase):
    def __init__(self, store=None, **kwargs):
        if store:
            store.add(self)

        cls = type(self)
        for attr, value in kwargs.items():
            if not hasattr(cls, attr):
                raise TypeError("class %s does not have an attribute %s" % (
                    cls.__name__, attr))

            # FIXME: storm is not setting foreign keys correctly if the
            # value is None (NULL)
            if value is not None:
                setattr(self, attr, value)

    def __eq__(self, other):
        if type(self) is not type(other):
            return False

        from stoqlib.lib.environment import is_developer_mode
        if is_developer_mode():
            # Check this only in develper mode to get as many potential errors
            # as possible.
            assert Store.of(self) is Store.of(other)
        return self.id == other.id

    def __ne__(self, other):
        return not self.__eq__(other)

    @property
    def store(self):
        return Store.of(self)
