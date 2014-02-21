# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
""" Sintegra generator dialog """

from dateutil.relativedelta import relativedelta
import gtk
from kiwi.ui.dialogs import save

from stoqlib.database.queryexecuter import QueryExecuter
from stoqlib.domain.system import SystemTable
from stoqlib.gui.base.dialogs import BasicDialog
from stoqlib.gui.search.searchfilters import DateSearchFilter
from stoqlib.lib.dateutils import get_month_names, localtoday
from stoqlib.lib.message import warning
from stoqlib.lib.sintegra import SintegraError
from stoqlib.lib.sintegragenerator import StoqlibSintegraGenerator
from stoqlib.lib.translation import stoqlib_gettext
_ = stoqlib_gettext


class SintegraDialog(BasicDialog):
    title = _('Fiscal Printer History')

    def __init__(self, store):
        BasicDialog.__init__(self, title=self.title)
        self.main_label.set_justify(gtk.JUSTIFY_CENTER)

        self.store = store
        self.ok_button.set_label(_("Generate"))

        self.date_filter = DateSearchFilter(_('Month:'))
        self.date_filter.set_use_date_entries(False)
        self.date_filter.clear_options()
        self._populate_date_filter(self.date_filter)
        self.date_filter.select()

        self.add(self.date_filter)
        self.date_filter.show()

    def confirm(self):
        start = self.date_filter.get_start_date()
        end = self.date_filter.get_end_date()
        filename = save(_("Save Sintegra file"),
                        self.get_toplevel(),
                        "sintegra-%s.txt" % (start.strftime('%Y-%m'), ))
        if not filename:
            return

        try:
            generator = StoqlibSintegraGenerator(self.store, start, end)
            generator.write(filename)
        except SintegraError as e:
            warning(str(e))
            return

        self.close()

    #
    # Private
    #

    def _populate_date_filter(self, date_filter):
        # The options we want to show to the users are the following:
        #   'May 2007'
        #   'June 2007'
        #   ...
        #   'September 2008'

        initial_date = self.store.find(SystemTable).min(
            SystemTable.updated).date()

        # Start is the first day of the month
        # End is the last day of the month
        start = initial_date + relativedelta(day=1)
        end = localtoday().date() + relativedelta(day=31)
        intervals = []
        while start < end:
            intervals.append((start, start + relativedelta(day=31)))
            start = start + relativedelta(months=1)

        # When we have the list of intervals, add them to the list and
        # make sure that they are translated
        month_names = get_month_names()
        for start, end in intervals:
            # Translators: Do not translate 'month' and 'year'. You can
            #              change it's positions. In the way it is,
            #              it will product for example 'December 2012'
            name = _('{month} {year}').format(
                month=month_names[start.month - 1],
                year=start.year)
            date_filter.add_option_fixed_interval(
                name, start, end, position=0)

    def _date_filter_query(self, search_spec, column):
        executer = QueryExecuter(self.store)
        executer.set_filter_columns(self.date_filter, [column])
        executer.set_table(search_spec)
        return executer.search([self.date_filter.get_state()])
