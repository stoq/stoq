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

import datetime
from kiwi.ui.objectlist import Column
from storm.expr import Desc

from stoqlib.gui.search.searchdialog import SearchDialog
from stoqlib.domain.event import Event
from stoqlib.lib.dateutils import pretty_date
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class EventSearch(SearchDialog):
    title = _('Search for events')
    size = (750, 500)
    search_spec = Event
    fast_iter = True

    def create_filters(self):
        self.set_text_field_columns(['description'])
        self.search.set_query(self.executer_query)

    def executer_query(self, store):
        return store.find(self.search_spec).order_by(Desc(Event.date))

    def get_columns(self):
        """Hook called by SearchEditor"""
        return [
            Column('event_type', title=_('Type'),
                   data_type=str, width=30,
                   format_func=lambda event_type: Event.types[event_type],
                   sort_func=self._sort_event_types),
            Column('description', title=_('Description'),
                   data_type=str, expand=True),
            Column('date', title=_('Date'),
                   data_type=datetime.datetime,
                   sorted=True,
                   format_func=pretty_date,
                   width=150)]

    def _sort_event_types(self, type_a, type_b):
        event_str_a = Event.types[type_a]
        event_str_b = Event.types[type_b]
        return cmp(event_str_a.lower(), event_str_b.lower())
