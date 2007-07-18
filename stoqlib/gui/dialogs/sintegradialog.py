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
## Author(s):       Johan Dahlin            <jdahlin@async.com.br>
##                  Fabio Morbec            <fabio@async.com.br>
##
""" Sintegra generator dialog """

import datetime

from dateutil.relativedelta import relativedelta
from kiwi.db.sqlobj import SQLObjectQueryExecuter
from kiwi.ui.dialogs import save
from kiwi.ui.search import DateSearchFilter

from stoqlib.gui.base.dialogs import ConfirmDialog
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.domain.system import SystemTable
from stoqlib.lib.message import warning
from stoqlib.lib.sintegra import SintegraError
from stoqlib.lib.sintegragenerator import StoqlibSintegraGenerator

_ = stoqlib_gettext

N_ = lambda x: x

month_names = {
    1: N_('January'),
    2: N_('February'),
    3: N_('March'),
    4: N_('April'),
    5: N_('May'),
    6: N_('June'),
    7: N_('July'),
    8: N_('August'),
    9: N_('September'),
    10: N_('October'),
    11: N_('November'),
    12: N_('December'),
}



class SintegraDialog(ConfirmDialog):
    size = (780, -1)
    title = _('Fiscal Printer History')

    def __init__(self, conn):
        ConfirmDialog.__init__(self)
        self.conn = conn
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
                        "sintegra-%s.txt" % (start.strftime('%Y-%m'),))
        if not filename:
            return

        try:
            generator = StoqlibSintegraGenerator(self.conn, start, end)
            generator.write(filename)
        except SintegraError, e:
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

        initial_date = SystemTable.select(
            connection=self.conn).min('updated').date()

        # Start is the first day of the month
        # End is the last day of the month
        start = initial_date + relativedelta(day=1)
        end = datetime.date.today() + relativedelta(day=31)
        intervals = []
        while start < end:
            intervals.append((start, start + relativedelta(day=31)))
            start = start + relativedelta(months=1)

        # When we have the list of intervals, add them to the list and
        # make sure that they are translated
        for start, end in intervals:
            # Translators: Month Year, eg: 'May 2007'
            name = _('%s %s') % (
                _(month_names[start.month]), start.year)
            date_filter.add_option_fixed_interval(
                name, start, end, position=0)

    def _date_filter_query(self, search_table, column):
        executer = SQLObjectQueryExecuter(self.conn)
        executer.set_filter_columns(self.date_filter, [column])
        executer.set_table(search_table)
        return executer.search([self.date_filter.get_state()])
