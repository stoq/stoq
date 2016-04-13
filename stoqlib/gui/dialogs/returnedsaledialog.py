# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2015-2016 Async Open Source <http://www.async.com.br>
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
""" Classes for returned sale dailgos (details and undo)"""

import gtk
from kiwi.currency import currency
from kiwi.ui.objectlist import Column
from storm.expr import Eq

from stoqlib.api import api
from stoqlib.domain.returnedsale import ReturnedSale, ReturnedSaleItem
from stoqlib.domain.views import ReturnedSalesView
from stoqlib.exceptions import StockError
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.gui.events import SaleReturnWizardFinishEvent
from stoqlib.gui.utils.printing import print_report
from stoqlib.lib.message import yesno, warning
from stoqlib.gui.search.searchcolumns import QuantityColumn
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.reporting.salereturn import PendingReturnReceipt

_ = stoqlib_gettext


class ReturnedSaleDialog(BaseEditor):
    """This dialog shows the details about pending returned sale

    * Sale Details
    * Invoice Details
    * Receiving Details
    """
    title = _("Returned Sale Details")
    hide_footer = True
    size = (850, 400)
    model_type = ReturnedSalesView
    report_class = PendingReturnReceipt
    # FIXME
    gladefile = "ReturnedSalesDetails"
    proxy_widgets = ['sale_identifier', 'invoice_number', 'returned_date',
                     'identifier', 'responsible_name', 'status_str']

    def _setup_status(self):
        self.receive_button.set_property('visible', self.model.can_receive())
        returned_sale = self.store.get(ReturnedSale, self.model.id)
        if not self.model.is_pending():
            self.receiving_responsible.set_text(returned_sale.confirm_responsible.person.name)
            self.receiving_date.update(returned_sale.confirm_date)

    def _update_reason(self):
        notes = [_('Return reason'), self.model.reason]
        if self.model.returned_sale.is_undone():
            notes.extend([_('Undo reason'), self.model.returned_sale.undo_reason])
        buffer = gtk.TextBuffer()
        buffer.set_text('\n\n'.join(notes))
        self.reason.set_buffer(buffer)

    def _setup_widgets(self):
        self._setup_status()
        returned_sale = self.model.returned_sale
        self.undo_button.set_sensitive(returned_sale.can_undo())

        self.returned_items_list.set_columns(self._get_returned_items_columns())
        r_items = returned_sale.returned_items
        for r_item in r_items.find(Eq(ReturnedSaleItem.parent_item_id, None)):
            self.returned_items_list.append(None, r_item)
            for child in r_item.children_items:
                self.returned_items_list.append(r_item, child)

        self._update_reason()

    def _get_returned_items_columns(self):
        return [Column("sellable.code", title=_("Product Code"), data_type=str,
                       width=130),
                Column("sellable.description", title=_("Description"),
                       data_type=str, expand=True),
                QuantityColumn("quantity", title=_("Qty returned")),
                Column("price", title=_("Price"), data_type=currency),
                Column("total", title=_("Total"), data_type=currency)]

    def _undo_returned_sale(self):
        returned_sale = self.model.returned_sale
        with api.new_store() as store:
            model = store.fetch(returned_sale)
            run_dialog(ReturnedSaleUndoDialog, self, store, model)

        if store.committed:
            self.model.sync()
            self.proxy.update('status_str')
            self.undo_button.set_sensitive(False)
            self._update_reason()

    #
    # BaseEditor Hooks
    #

    def setup_proxies(self):
        self._setup_widgets()
        self.proxy = self.add_proxy(self.model, self.proxy_widgets)

    #
    # Callbacks
    #

    def on_receive_button__clicked(self, event):
        if yesno(_(u'Receive pending returned sale?'), gtk.RESPONSE_NO,
                 _(u'Receive'), _(u"Don't receive")):
            current_user = api.get_current_user(self.store)
            self.model.returned_sale.confirm(current_user)
            SaleReturnWizardFinishEvent.emit(self.model.returned_sale)
            self.store.commit(close=False)
            self._setup_status()

    def on_print_button__clicked(self, button):
        print_report(self.report_class, self.model)

    def on_undo_button__clicked(self, button):
        # TODO: Verificar status
        self._undo_returned_sale()


class ReturnedSaleUndoDialog(BaseEditor):
    title = _("Undo Returned Sale")
    size = (450, 200)
    model_type = ReturnedSale
    gladefile = "ReturnedSaleUndoDialog"

    def __init__(self, store, model):
        BaseEditor.__init__(self, store, model)
        self.main_dialog.set_ok_label(_('Undo Returned Sale'))
        self.main_dialog.set_cancel_label(_("Don't Undo"))
        # The user should fill the reason.
        self.main_dialog.ok_button.set_sensitive(False)

    def on_undo_reason__content_changed(self, widget):
        reason = self.undo_reason.read()
        self.main_dialog.ok_button.set_sensitive(bool(reason))

    def confirm(self):
        try:
            self.model.undo(reason=self.undo_reason.read())
        except StockError:
            warning(_('It was not possible to undo this returned sale. Some of '
                      'the returned products are out of stock.'))
            return self.cancel()
        return super(ReturnedSaleUndoDialog, self).confirm()
