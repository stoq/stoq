#
# Copyright (C) 2020 Stoq Tecnologia <http://www.stoq.com.br>
# All rights reserved
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., or visit: http://www.gnu.org/.
#
#  Author(s): Stoq Team <stoq-devel@async.com.br>
#

from zope.interface import implementer, Attribute, Interface

# pyflakes
implementer, Attribute, Interface

ValueUnset = object()


class AlreadyImplementedError(Exception):
    """Called when a utility already exists."""


class _UtilityHandler:
    def __init__(self):
        self._utilities = {}

    # FIXME: How to replace a utility properly
    def provide(self, iface, obj, replace=False):
        if not issubclass(iface, Interface):
            raise TypeError(
                "iface must be an Interface subclass and not %r" % iface)

        if not replace:
            if iface in self._utilities:
                raise AlreadyImplementedError("%s is already implemented" % iface)
        self._utilities[iface] = obj

    def get(self, iface, default):
        if not issubclass(iface, Interface):
            raise TypeError(
                "iface must be an Interface subclass and not %r" % iface)

        if not iface in self._utilities:
            if default is ValueUnset:
                raise NotImplementedError("No utility provided for %r" % iface)
            else:
                return default

        return self._utilities[iface]

    def remove(self, iface):
        if not issubclass(iface, Interface):
            raise TypeError(
                "iface must be an Interface subclass and not %r" % iface)

        if not iface in self._utilities:
            raise NotImplementedError("No utility provided for %r" % iface)

        return self._utilities.pop(iface)

    def clean(self):
        self._utilities = {}


def provide_utility(iface, utility, replace=False):
    """
    Set the utility for the named interface. If the utility is already
    set, an {AlreadyImplementedError} is raised.

    :param iface: interface to set the utility for.
    :param utility: utility providing the interface.
    """
    utilities.provide(iface, utility, replace)


def get_utility(iface, default=ValueUnset):
    """
    Get the utility for the named interface. If the utility is not
    available (has not been set) a {NotImplementedError} is raised unless
    default is set.

    :param iface: an interface
    :param default: optional, if set return if a utility is not found
    :returns: the utility
    """

    return utilities.get(iface, default)


def remove_utility(iface):
    """
    Remove the utility provided for an interface
    If the utility is not available (has not been set)
    {NotImplementedError} is raised.

    :param iface: the interface
    :returns: the removed utility
    """

    return utilities.remove(iface)


utilities = _UtilityHandler()
