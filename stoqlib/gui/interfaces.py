# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007-2013 Async Open Source
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

# pylint: disable=E0102,E0211,E0213

from zope.interface import Interface


class IDomainSlaveMapper(Interface):
    """
    This is a singleton responsible for mapping
    a domain object to a slave.
    """

    def register(domain_class, slave_class):
        """Register a slave class for a domain class.
        :param domain_class:
        :param slave_class:
        """

    def get_slave_class(domain_class):
        """Fetch a slave class given a domain class.
        :param domain_class:
        :returns: the slave class or None
        """


class ISearchResultView(Interface):
    """
    This is an interface that displays the results
    of a search query, done by a search container

    In addition to the interfaces above, the following GObject signals needs to be implemented:

    - item-activated (item)
    - item-popup-menu (item, event)
    - selection-changed ()

    """

    def attach(container, columns):
        """
        This is called after we've been attached to a search container

        :param SearchContainer container: the search container
        :param columns: list of objectlist columns
        """

    def enable_lazy_search():
        """
        Enables lazy search for this view,
        it only makes sense when the items are displayed in
        an ObjectList
        """

    def show():
        """
        Displays the result view
        """

    def clear():
        """
        Clears the results
        """

    def search_completed(results):
        """
        The search was completed. This should populate the widget
        with the new information.

        :param results: a result set
        """

    def get_n_items():
        """
        :returns: now many items there are in the view
        """

    def get_selected_item():
        """
        Fetches the currently selected item

        :return: the selected item
        """

    def get_settings():
        """
        Serialize the internal settings for this view

        :returns: the settings for this view
        :rtype: a dictionary
        """

    def destroy():
        """
        Destroys the result view
        """

    # FIXME: Move these over to search itself of having an implementation
    #        on each view. We might be able to kill the ObjectList variants
    #        as well with these changes.

    def set_message(message):
        pass

    def clear_message():
        pass

# pylint: enable=E0102,E0211,E0213
