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
##
""" Fiscal Printer History dialog """

import datetime

from dateutil.relativedelta import relativedelta
import gtk
from kiwi.db.sqlobj import SQLObjectQueryExecuter
from kiwi.ui.dialogs import save
from kiwi.ui.search import DateSearchFilter

from stoqlib.database.runtime import get_current_branch
from stoqlib.domain.devices import FiscalDayHistory
from stoqlib.domain.interfaces import ICompany
from stoqlib.domain.system import SystemTable
from stoqlib.gui.base.dialogs import ConfirmDialog
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.sintegra import SintegraFile

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

    def setup_widgets(self):
        self.results.set_visible_rows(10)
        b = gtk.Button(_('_Generate archive'))
        b.connect('clicked', self._on_generate__clicked)
        b.set_use_underline(True)
        self.action_area.set_layout(gtk.BUTTONBOX_START)
        self.action_area.pack_start(b, False, False, 6)
        b.show()
        has_start_date = bool(self.date_filter.get_start_date())
        b.set_sensitive(has_start_date)

    def confirm(self):
        start = self.date_filter.get_start_date()
        end = self.date_filter.get_end_date()
        filename = save(_("Save Sintegra file"),
                        self.get_toplevel(),
                        "sintegra-%s.txt" % (start.strftime('%Y-%m'),))
        if filename:
            sfile = self._generate_sintegra(start, end)
            sfile.write(filename)
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

    def _generate_sintegra(self, start, end):
        branch = get_current_branch(self.conn)
        company = ICompany(branch.person)
        address = branch.person.get_main_address()

        s = SintegraFile()
        s.add_header(company.get_cnpj_number(),
                     str(company.get_state_registry_number()) or 'ISENTO',
                     company.fancy_name,
                     address.get_city(),
                     address.get_state(),
                     branch.person.get_fax_number_number(),
                     start, end)
        s.add_complement_header(address.street, address.number,
                                address.complement,
                                address.district,
                                address.get_postal_code_number(),
                                company.fancy_name,
                                branch.person.get_phone_number_number())

        self._add_fiscal_coupons(s, start, end)
        s.close()

        return s

    def _add_fiscal_coupons(self, sintegra, start, end):
        for item in self._date_filter_query(FiscalDayHistory, 'emission_date'):
            sintegra.add_fiscal_coupon(
                item.emission_date, item.serial, item.serial_id,
                item.coupon_start, item.coupon_end,
                item.cro, item.crz, item.period_total, item.total)
            for tax in item.taxes:
                sintegra.add_fiscal_tax(item.emission_date, item.serial,
                                        tax.code, tax.value)

