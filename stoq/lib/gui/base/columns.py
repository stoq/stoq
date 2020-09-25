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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
""" Special columns definition for kiwi lists """

from kiwi.ui.objectlist import Column


class AccessorColumn(Column):
    def __init__(self, attribute, accessor, *args, **kwargs):
        if not accessor:
            raise TypeError('AccessorColumn needs an accessor argument')

        self.accessor = accessor
        assert callable(self.accessor)
        Column.__init__(self, attribute=attribute, *args, **kwargs)

    def get_attribute(self, instance, name, default=None):
        return self.accessor(instance)
