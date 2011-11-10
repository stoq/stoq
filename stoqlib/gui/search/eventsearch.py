# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2007 Async Open Source <http://www.async.com.br>
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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##
""" Implementation of event search """

from kiwi.ui.objectlist import Column

from stoqlib.gui.base.search import SearchEditor
from stoqlib.domain.event import Event
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.prettydate import pretty_date

_ = stoqlib_gettext


class EventSearch(SearchEditor):
    title = _('Search for events')
    size = (750, 500)
    table = search_table = Event
    editor_class = None
    #model_list_lookup_attr = 'product_id'
    searchbar_result_strings = (_('event'), _('events'))

    def create_filters(self):
        self.set_text_field_columns(['description'])

    def get_columns(self):
        """Hook called by SearchEditor"""
        return [
            Column('event_type', title=_('Type'),
                   data_type=str, width=30,
                   format_func=lambda event_type: Event.types[event_type]),
            Column('description', title=_('Description'),
                   data_type=str, expand=True),
            Column('date', title=_('Date'),
                   data_type=str,
                   sorted=True,
                   format_func=pretty_date,
                   width=150, searchable=True)]
