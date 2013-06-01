# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2008 Async Open Source <http://www.async.com.br>
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

"""A domain to slave singleton mapper
"""

from zope.interface import implementer

from stoqlib.gui.interfaces import IDomainSlaveMapper


@implementer(IDomainSlaveMapper)
class DefaultDomainSlaveMapper(object):
    def __init__(self):
        self._slave_classes = {}

    def register(self, domain, slave_class):
        self._slave_classes[(type(domain), domain.id)] = slave_class

    def get_slave_class(self, domain):
        return self._slave_classes.get((type(domain), domain.id))
