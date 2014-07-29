# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
##
## Copyright (C) 2014 Async Open Source <http://www.async.com.br>
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

""" Search dialog/Editor for publishers """

import datetime
import decimal

from kiwi.currency import currency

from stoqlib.domain.sale import Sale
from stoqlib.enums import SearchFilterPosition
from stoqlib.lib.formatters import format_quantity
from stoqlib.domain.sale import SaleView
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.dialogs.saledetails import SaleDetailsDialog
from stoqlib.gui.search.personsearch import BasePersonSearch
from stoqlib.gui.search.searchcolumns import SearchColumn, IdentifierColumn
from stoqlib.gui.search.searchfilters import DateSearchFilter
from stoqlib.gui.search.searchdialog import SearchDialog
from stoqlib.lib.translation import stoqlib_gettext

from optical.opticaldomain import OpticalMedicView, MedicSoldItemsView
from optical.opticalslave import MedicEditor

_ = stoqlib_gettext


class OpticalMedicSearch(BasePersonSearch):
    title = _('Medic Search')
    editor_class = MedicEditor
    search_spec = OpticalMedicView
    size = (750, 450)
    search_lbl_text = _('Medic matching:')
    result_strings = _('medic'), _('medics')

    #
    # SearchDialog Hooks
    #

    def create_filters(self):
        self.set_text_field_columns(['name', 'phone_number', 'crm_number'])

    def get_columns(self):
        return [SearchColumn('name', title=_('Medic Name'), sorted=True,
                             data_type=str, expand=True),
                SearchColumn('phone_number', title=_('Phone Number'),
                             data_type=str),
                SearchColumn('crm_number', title=_('UPID'),
                             data_type=str),
                SearchColumn('partner', title=_('Partner'), data_type=bool,
                             visible=False)]

    def get_editor_model(self, model):
        return model.medic


class MedicSalesSearch(SearchDialog):
    title = _(u'Sold Items by medic')
    size = (800, 450)
    search_spec = MedicSoldItemsView
    fast_iter = True

    #
    # SearchDialog Hooks
    #

    def setup_widgets(self):
        self.add_csv_button(_('Sold Products'), _('sold-products'))
        self.sale_details_button = self.add_button(label=_('Sale Details'))
        self.sale_details_button.show()
        self.sale_details_button.set_sensitive(False)

    def update_widgets(self):
        item = self.results.get_selected()
        self.sale_details_button.set_sensitive(bool(item))

    def create_filters(self):
        self.set_text_field_columns(['medic_name', 'description', 'code'])

        # Dont set a limit here, otherwise it might break the summary
        executer = self.search.get_query_executer()
        executer.set_limit(-1)

        branch_filter = self.create_branch_filter(_('In Branch:'))
        self.add_filter(branch_filter, SearchFilterPosition.TOP,
                        columns=[Sale.branch_id])

        self._date_filter = DateSearchFilter(_("Date:"))
        self._date_filter.select(data=DateSearchFilter.Type.USER_INTERVAL)
        self.add_filter(self._date_filter, SearchFilterPosition.BOTTOM,
                        columns=[Sale.confirm_date])
        self.search.set_summary_label('total', label=_(u'Total:'),
                                      format='<b>%s</b>')

    def get_columns(self):
        columns = [
            IdentifierColumn('identifier', title=_('Sale #')),
            SearchColumn('open_date', title=_('Open date'),
                         data_type=datetime.date, visible=False),
            SearchColumn('confirm_date', title=_('Confirm date'),
                         data_type=datetime.date, visible=False),
            SearchColumn('code', title=_('Code'), data_type=str, sorted=True),
            SearchColumn('category', title=_('Category'), data_type=str, visible=False),
            SearchColumn('branch_name', title=_('Branch'), data_type=str,
                         visible=False),
            SearchColumn('description', title=_('Description'), data_type=str,
                         expand=True),
            SearchColumn('manufacturer', title=_('Manufacturer'), data_type=str,
                         visible=False),
            SearchColumn('medic_name', title=_('Medic'), data_type=str),
            SearchColumn('crm_number', title=_('CRM'), data_type=str),
            SearchColumn('partner', title=_('Partner'), data_type=bool,
                         visible=False, width=40),
            SearchColumn('batch_number', title=_('Batch'), data_type=str,
                         visible=False),
            SearchColumn('batch_date', title=_('Batch Date'),
                         data_type=datetime.date, visible=False),
            SearchColumn('quantity', title=_('Qty'), data_type=decimal.Decimal,
                         format_func=format_quantity),
            SearchColumn('total', title=_('Total'), data_type=currency),
        ]

        return columns

    def on_sale_details_button__clicked(self, widget):
        item = self.results.get_selected()
        sale_view = self.store.find(SaleView, id=item.sale_id).one()
        run_dialog(SaleDetailsDialog, self, self.store, sale_view)
