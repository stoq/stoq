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
    def get_slave():
        pass

    def get_search_string():
        pass

    def set_search_string(search_str):
        pass

    def set_search_label(search_entry_lbl, date_search_lbl=None):
        pass

    def start_animate_search_icon():
        pass

    def stop_animate_search_icon():
        pass

    def clear():
        pass

    def get_extra_queries():
        pass

