# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013 Async Open Source <http://www.async.com.br>
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

import collections

from stoqlib.database.queryexecuter import DateQueryState
from stoqlib.gui.base.dialogs import BasicDialog
from stoqlib.gui.search.searchfilters import DateSearchFilter
from stoqlib.gui.search.searchoptions import Today, Yesterday, LastWeek, LastMonth
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext

#: returned by :class:`DateRangeDialog` containing information about
#: the date range selected in it
date_range = collections.namedtuple('date_range', ['start', 'end'])


class DateRangeDialog(BasicDialog):
    """A simple dialog for selecting a date range

    When confirmed, a :class:`date_range` object will be returned
    containig the information about the date range selected
    """

    title = _(u'Select a date range')
    size = (-1, -1)

    def __init__(self, title=None, header_text=None):
        title = title or self.title
        header_text = '<b>%s</b>' % header_text if header_text else ''
        BasicDialog.__init__(self, title=title, header_text=header_text)

        self._setup_widgets()

    #
    #  BasicDialog
    #

    def confirm(self):
        BasicDialog.confirm(self)

        state = self.date_filter.get_state()
        if isinstance(state, DateQueryState):
            start, end = state.date, state.date
        else:
            start, end = state.start, state.end

        self.retval = date_range(start=start, end=end)

    #
    #  Private
    #

    def _setup_widgets(self):
        self.date_filter = DateSearchFilter(_(u'Date:'))
        # FIXME: add a remove_option method in DateSearchFilter.
        self.date_filter.clear_options()
        self.date_filter.add_custom_options()
        for option in [Today, Yesterday, LastWeek, LastMonth]:
            self.date_filter.add_option(option)
        self.date_filter.select(position=0)

        self.vbox.pack_start(self.date_filter, False, False)
        self.date_filter.show_all()
