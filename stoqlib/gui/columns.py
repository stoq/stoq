# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2004 Async Open Source <http://www.async.com.br>
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
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
"""
gui/columns.py:

    Special columns definition for kiwi lists.
"""

from twisted.python.components import Adapter
from kiwi.accessors import kgetattr
from kiwi.ui.widgets.list import Column
 
class FacetColumn(Column):
    def __init__(self, facet, *args, **kwargs):
        self._facet = facet
        Column.__init__(self, *args, **kwargs)
 
    def get_attribute(self, instance, name, default=None):
        if not isinstance(instance, Adapter):
            obj = self._facet(instance)
        else:
            original = instance.get_adapted()
            conn = instance.get_connection()
            obj = self._facet(original, connection=conn)
        return kgetattr(obj, name, default)

    def get_facet(self):
        return self._facet

class ForeignKeyColumn(Column):
    def __init__(self, table, *args, **kwargs):
        if not 'obj_field' in kwargs:
            raise TypeError('ForeigKeyColumn needs an obj_field argument')
 
        self._table = table
        self._obj_field = kwargs.pop('obj_field')
        Column.__init__(self, *args, **kwargs)
 
    def get_attribute(self, instance, name, default=None):
        attr = '%s.%s' % (self._obj_field, name)
        return kgetattr(instance, attr, default)

class AccessorColumn(Column):
    def __init__(self, attribute, accessor, *args, **kwargs):
        if not accessor:
            raise TypeError('AccessorColumn needs an accessor argument')
 
        self.accessor = accessor
        assert callable(self.accessor)
        Column.__init__(self, attribute=attribute, *args, **kwargs)
 
    def get_attribute(self, instance, name, default=None):
        return self.accessor(instance)
