# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007 Async Open Source
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
## Author(s):   Johan Dahlin      <jdahlin@async.com.br>
##

from zope.interface import Interface

class ISearchBarEntrySlave(Interface):
    """
    This interface represents a slave which you can embed in a SearchBar.
    """

    def get_slave():
        """
        Returns the slave which we embed in the search bar
        """

    def start_animation():
        """
        Start the search animation. This is called when a search is begun.
        """

    def stop_animation():
        """
        Stop the search animation. This is called after a search is done.
        """

    def clear():
        """
        Clear all interactive widgets inside the slave
        """

    def get_extra_queries():
        """
        Return a list of queries that will be combined with an AND in
        the searchbar itself.
        It can return an empty list if desired.
        """

    def get_search_string():
        pass

    def set_search_string(search_str):
        pass

    def set_search_label(label):
        pass

