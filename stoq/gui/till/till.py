# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2007 Async Open Source <http://www.async.com.br>
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
## Author(s):       Henrique Romano             <henrique@async.com.br>
##                  Evandro Vale Miquelito      <evandro@async.com.br>
##                  Johan Dahlin                <jdahlin@async.com.br>
##
""" Implementation of till application.  """

import gettext
import decimal
from datetime import date

import pango
import gtk
from kiwi.datatypes import currency, converter
from kiwi.log import Logger
from kiwi.enums import SearchFilterPosition
from kiwi.ui.search import DateSearchFilter, ComboSearchFilter
from kiwi.ui.widgets.list import Column
from stoqlib.exceptions import StoqlibError, TillError
from stoqlib.database.runtime import (new_transaction, get_current_branch,
                                      rollback_and_begin, finish_transaction)
from stoqlib.domain.interfaces import IPaymentGroup
from stoqlib.domain.sale import Sale, SaleView
from stoqlib.domain.till import Till
from stoqlib.drivers.cheque import print_cheques_for_payment_group
from stoqlib.lib.message import yesno
from stoqlib.lib.validators import format_quantity
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.dialogs.tillhistory import TillHistoryDialog
from stoqlib.gui.dialogs.saledetails import SaleDetailsDialog
from stoqlib.gui.editors.tilleditor import CashInEditor, CashOutEditor
from stoqlib.gui.fiscalprinter import FiscalPrinterHelper
from stoqlib.gui.search.personsearch import ClientSearch
from stoqlib.gui.search.salesearch import SaleSearch
from stoqlib.gui.search.tillsearch import TillFiscalOperationsSearch
from stoqlib.gui.wizards.salewizard import ConfirmSaleWizard
from stoqlib.gui.wizards.salereturnwizard import SaleReturnWizard

from stoq.gui.application import SearchableAppWindow

_ = gettext.gettext
log = Logger('stoq.till')


class TillApp(SearchableAppWindow):

    app_name = _(u'Till')
    app_icon_name = 'stoq-till-app'
    gladefile = 'till'
    search_table = SaleView
    search_labels = _(u'matching:')

    def __init__(self, app):
        SearchableAppWindow.__init__(self, app)
        self._printer = FiscalPrinterHelper(
            self.conn, parent=self.get_toplevel())
        self._setup_widgets()
        self.refresh()
        self._update_widgets()

    #
    # SearchableAppWindow hooks
    #

    def setup_focus(self):
        # Groups
        self.main_vbox.set_focus_chain([self.app_vbox])
        self.app_vbox.set_focus_chain([self.search_holder, self.list_vbox])

        # Setting up the toolbar
        self.list_vbox.set_focus_chain([self.footer_hbox])
        self.footer_hbox.set_focus_chain([self.confirm_order_button,
                                          self.return_button,
                                          self.details_button])

    def create_filters(self):
        self.set_text_field_columns(['client_name', 'salesperson_name'])
        date_filter = DateSearchFilter(_('Paid or due date:'))
        self.add_filter(
            date_filter, columns=['open_date'])
        status_filter = ComboSearchFilter(_(u"Show orders with status"),
                                          self._get_status_values())
        status_filter.select(Sale.STATUS_CONFIRMED)
        self.add_filter(status_filter, position=SearchFilterPosition.TOP,
                        columns=['status'])

    def get_title(self):
        return _('Stoq - Till for Branch %03d') % get_current_branch(self.conn).id

    def get_columns(self):
        return [Column('id', title=_('Number'), width=80,
                       data_type=int, format='%05d', sorted=True),
                Column('open_date', title=_('Date Started'), width=120,
                       data_type=date, justify=gtk.JUSTIFY_RIGHT),
                Column('client_name', title=_('Client'),
                       data_type=str, width=160, expand=True,
                       ellipsize=pango.ELLIPSIZE_END),
                Column('salesperson_name', title=_('Salesperson'),
                       data_type=str, width=160,
                       ellipsize=pango.ELLIPSIZE_END),
                Column('total_quantity', title=_('Quantity'),
                       data_type=decimal.Decimal, width=100,
                       format_func=format_quantity),
                Column('total', title=_('Total'), data_type=currency,
                       width=120)]

    #
    # Till methods
    #

    def _open_till(self):
        if self._printer.open_till():
            self._update_widgets()

    def _close_till(self, can_remove_cash=True):
        retval = self._printer.close_till(can_remove_cash)
        if retval:
            self._update_widgets()
        return retval

    #
    # Private
    #

    def _get_status_values(self):
        statuses = [(v, k) for k, v in Sale.statuses.items()]
        statuses.insert(0, (_('Any'), None))
        return statuses

    def _confirm_order(self):
        rollback_and_begin(self.conn)
        selected = self.results.get_selected()
        sale = Sale.get(selected.id, connection=self.conn)
        title = _('Confirm Sale')
        model = self.run_dialog(ConfirmSaleWizard, self.conn, sale)
        if not finish_transaction(self.conn, model):
            return
        if not self._printer.emit_coupon(sale):
            return
        sale.confirm()

        if sale.paid_with_money():
            sale.set_paid()

        print_cheques_for_payment_group(self.conn, IPaymentGroup(sale))

        self.conn.commit()
        self.refresh()

    def _summary(self):
        self._printer.summarize()

    def _update_total(self):
        if len(self.results):
            totals = [sale.total for sale in self.results]
            subtotal = currency(sum(totals, currency(0)))
        else:
            subtotal = currency(0)
        text = _(u"Total: %s") % converter.as_string(currency, subtotal)
        self.total_label.set_text(text)

    def _setup_widgets(self):
        self.total_label.set_size('xx-large')
        self.total_label.set_bold(True)
        self.till_status_label.set_size('large')
        self.till_status_label.set_bold(True)

    def _update_toolbar_buttons(self):
        sale_view = self.results.get_selected()
        if sale_view:
            can_confirm = sale_view.sale.can_confirm()
            can_return = sale_view.sale.can_return()
        else:
            can_confirm = can_return = False

        self.details_button.set_sensitive(bool(sale_view))
        self.confirm_order_button.set_sensitive(can_confirm)
        self.return_button.set_sensitive(can_return)

    def _update_widgets(self):
        # Three different options;
        #
        # - Till is closed
        # - Till is opened
        # - Till was not closed the previous fiscal day
        #

        try:
            till = Till.get_current(self.conn)
        except TillError:
            till = Till.get_last_opened(self.conn)
            # We forgot to close the till the last opened day
            close_till = True
            open_till = False
            has_till = False
        else:
            has_till = bool(till)
            close_till = has_till
            open_till = not has_till

        self.TillClose.set_sensitive(close_till)
        self.TillOpen.set_sensitive(open_till)
        self.AddCash.set_sensitive(has_till)
        self.RemoveCash.set_sensitive(has_till)
        self.TillHistory.set_sensitive(has_till)

        if not till:
            text = _(u"Till Closed")
            self.clear()
            self.setup_focus()
        else:
            text = _(u"Till Opened on %s") % till.opening_date.strftime('%x')

        self.till_status_label.set_text(text)
        self.app_vbox.set_sensitive(has_till)

        self._update_toolbar_buttons()
        self._update_total()

    def _check_selected(self):
        sale_view = self.results.get_selected()
        if not sale_view:
            raise StoqlibError("You should have a selected item at "
                               "this point")
        return sale_view

    def _run_search_dialog(self, dialog_type, **kwargs):
        trans = new_transaction()
        self.run_dialog(dialog_type, trans, **kwargs)
        trans.close()

    def _run_details_dialog(self):
        sale_view = self._check_selected()
        run_dialog(SaleDetailsDialog, self, self.conn, sale_view)

    #
    # Actions
    #

    def _on_close_till_action__clicked(self, button):
        if not yesno(_(u"You can only close the till once per day. "
                       "\n\nClose the till?"),
                     gtk.RESPONSE_NO, _(u"Not now"), _("Close Till")):
            if not self._close_till():
                return False

    def _on_open_till_action__clicked(self, button):
        self._open_till()

    def _on_client_search_action__clicked(self, button):
        self._run_search_dialog(ClientSearch, hide_footer=True)

    def _on_sale_search_action__clicked(self, button):
        self._run_search_dialog(SaleSearch)

    def _on_fiscal_till_operations__action_clicked(self, button):
        self._run_search_dialog(TillFiscalOperationsSearch)

    def on_TillHistory__activate(self, button):
        dialog = TillHistoryDialog(self.conn)
        self.run_dialog(dialog, self.conn)

    def on_AddCash__activate(self, action):
        model = run_dialog(CashInEditor, self, self.conn)
        finish_transaction(self.conn, model)

    def on_RemoveCash__activate(self, action):
        model = run_dialog(CashOutEditor, self, self.conn)
        finish_transaction(self.conn, model)

    #
    # Callbacks
    #

#     def on_searchbar_activate(self, slave, objs):
#         SearchableAppWindow.on_searchbar_activate(self, slave, objs)
#         self._update_toolbar_buttons()
#         self._update_total()

    #
    # Kiwi callbacks
    #

    def on_confirm_order_button__clicked(self, button):
        self._confirm_order()

    def on_results__double_click(self, results, sale):
        self._run_details_dialog()

    def on_results__selection_changed(self, results, sale):
        self._update_toolbar_buttons()

    def on_details_button__clicked(self, button):
        self._run_details_dialog()

    def on_return_button__clicked(self, button):
        sale_view = self._check_selected()
        retval = run_dialog(SaleReturnWizard, self, self.conn, sale_view)
        finish_transaction(self.conn, retval)
