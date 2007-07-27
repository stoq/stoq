# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007 Async Open Source <http://www.async.com.br>
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
##  Author(s):  George Kussumoto    <george@async.com.br>
##
""" Search dialogs for commission objects """

from decimal import Decimal

from kiwi.datatypes import currency
from kiwi.enums import SearchFilterPosition
from kiwi.ui.search import ComboSearchFilter, DateSearchFilter
from kiwi.ui.widgets.list import Column

from stoqlib.domain.commission import CommissionView
from stoqlib.domain.interfaces import ISalesPerson
from stoqlib.domain.person import Person
from stoqlib.gui.base.search import SearchDialog
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class CommissionSearch(SearchDialog):
    title = _("Search for Commissions")
    size = (750, 450)
    search_table = CommissionView
    searching_by_date = True

    #
    # SearchDialog Hooks
    #

    def create_filters(self):
        self.set_text_field_columns(['salesperson_name', 'id'])
        self.set_searchbar_labels(_('matching:'))

        persons = [p.get_adapted().name for p in
                   Person.iselect(ISalesPerson, connection=self.conn)]
        persons = zip(persons, persons)
        persons.insert(0, (_('Anyone'), None))
        salesperson_filter = ComboSearchFilter(_('Sold By:'), persons)
        self.add_filter(salesperson_filter, SearchFilterPosition.TOP,
                        ['salesperson_name'])

        date_filter = DateSearchFilter(_('Open date is:'))
        self.add_filter(date_filter, SearchFilterPosition.BOTTOM, ['open_date'])

    def get_columns(self):
        return [Column('id', title=_('Sale'),
                        data_type=int, sorted=True),
                Column('salesperson_name', title=_('Salesperson'),
                        data_type=str, expand=True),
                Column('commission_percentage', title=_('Commission (%)'),
                        data_type=Decimal, format="%.2f"),
                Column('commission_value', title=_('Commission'),
                        data_type=currency),
                Column('payment_amount', title=_('Payment Value'),
                        data_type=currency),
                Column('total_amount', title=_('Sale Total'),
                        data_type=currency)]
