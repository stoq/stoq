# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007-2008 Async Open Source
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

from zope.interface import Interface


class IDomainSlaveMapper(Interface):
    """
    This is a singleton responsible for mapping
    a domain object to a slave.
    """

    def register(domain_class, slave_class):
        """Register a slave class for a domain class.
        @param domain_class:
        @param slave_class:
        """

    def get_slave_class(domain_class):
        """Fetch a slave class given a domain class.
        @param domain_class:
        @returns: the slave class or None
        """
