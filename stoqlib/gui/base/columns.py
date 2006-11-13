# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005, 2006 Async Open Source
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
""" Special columns definition for kiwi lists """

from kiwi.accessor import kgetattr
from kiwi.ui.widgets.list import Column

from stoqlib.lib.component import Adapter


class FacetColumn(Column):
    def __init__(self, iface, *args, **kwargs):
        self._iface = iface
        Column.__init__(self, *args, **kwargs)

    def get_attribute(self, instance, name, default=None):
        if not isinstance(instance, Adapter):
            facet = self._iface(instance, None)
        else:
            original = instance.get_adapted()
            facet = self._iface(original, None)
        if not facet:
            return
        return kgetattr(facet, name, default)

    def get_iface(self):
        return self._iface

class ForeignKeyColumn(Column):
    """
    ForeignKeyColumn is a special column which is normally used together
    with a foreign key, for an sqlobject table.
    """
    def __init__(self, table, *args, **kwargs):
        """
        Need an obj_field or adapted argument.
        See L{kiwi.ui.widgets.list.Column} for other arguments
        @keyword obj_field: attribute name or None
        @keyword adapted: if the attribute should be adapted or not, in
          practice this means the original object will be fetched.
        """
        if not 'obj_field' in kwargs and not 'adapted' in kwargs:
            raise TypeError(
                'ForeigKeyColumn needs an obj_field or adapted argument')

        self._table = table
        self._obj_field = kwargs.pop('obj_field', None)
        self._adapted = kwargs.pop('adapted', False)
        Column.__init__(self, *args, **kwargs)

    def get_attribute(self, instance, name, default=None):
        if self._obj_field:
            value = kgetattr(instance, self._obj_field, default)
            if value is None:
                return
        else:
            value = instance

        if self._adapted:
            value = value.get_adapted()
        return kgetattr(value, name, default)

class AccessorColumn(Column):
    def __init__(self, attribute, accessor, *args, **kwargs):
        if not accessor:
            raise TypeError('AccessorColumn needs an accessor argument')

        self.accessor = accessor
        if not kwargs.has_key('cache'):
            kwargs['cache'] = True
        assert callable(self.accessor)
        Column.__init__(self, attribute=attribute, *args, **kwargs)

    def get_attribute(self, instance, name, default=None):
        return self.accessor(instance)
