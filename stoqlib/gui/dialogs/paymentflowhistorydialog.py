# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2010 Async Open Source <http://www.async.com.br>
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
"""Payment Flow History Report Dialog"""


import gtk
from kiwi.python import Settable
from kiwi.ui.search import (DateSearchFilter, Today, Yesterday, LastWeek,
                            LastMonth)

from stoqlib.database.orm import ORMObjectQueryExecuter
from stoqlib.domain.payment.payment import PaymentFlowHistory
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.gui.printing import print_report
from stoqlib.lib.message import info
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.reporting.payment import PaymentFlowHistoryReport

_ = stoqlib_gettext


class PaymentFlowHistoryDialog(BaseEditor):
    gladefile = 'PaymentFlowHistoryDialog'
    title = _(u'Payment Flow History Dialog')
    size = (600, 150)
    model_type = Settable

    def __init__(self, conn):
        """A dialog to print the PaymentFlowHistoryReport report.

        @param conn: a database connection
        """
        executer = ORMObjectQueryExecuter(conn)
        executer.set_table(PaymentFlowHistory)
        model = Settable(executer=executer)
        self.conn = conn
        BaseEditor.__init__(self, conn, model=model)
        self._setup_widgets()

    #
    # BaseEditor
    #

    def validate_confirm(self):
        results = self.model.executer.search([self._date_filter.get_state()])
        if results:
            ordered = results.orderBy(PaymentFlowHistory.q.history_date)
            print_report(PaymentFlowHistoryReport, payment_histories=ordered)
            return True
        else:
            info(_(u'No payment history found.'))

    #
    # Private
    #

    def _setup_widgets(self):
        self.main_dialog.ok_button.set_label(gtk.STOCK_PRINT)

        self._date_filter = DateSearchFilter(_(u'Date:'))
        #FIXME: add a remove_option method in DateSearchFilter.
        self._date_filter.clear_options()
        self._date_filter.add_custom_options()
        for option in [Today, Yesterday, LastWeek, LastMonth]:
            self._date_filter.add_option(option)
        self._date_filter.select(position=0)

        self.model.executer.set_filter_columns(self._date_filter,
                                               ['history_date'])
        self.date_box.pack_start(self._date_filter, False, False)
        self._date_filter.show()
