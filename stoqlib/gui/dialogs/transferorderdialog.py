# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007-2015 Async Open Source <http://www.async.com.br>
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
""" Classes for Transfer Order Details Dialog """

import gtk
from kiwi.currency import currency
from kiwi.ui.objectlist import Column, SummaryLabel

from stoqlib.api import api
from stoqlib.domain.transfer import TransferOrder, TransferOrderItem
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.gui.utils.printing import print_report
from stoqlib.lib.message import yesno
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.reporting.transfer import TransferOrderReceipt

_ = stoqlib_gettext


class TransferOrderDetailsDialog(BaseEditor):
    """This dialog shows some important details about transfer orders
    like:

    * The source and destination branches
    * The transfer quantity of each item
    * The cost of each item
    """

    title = _(u"Transfer Order Details")
    hide_footer = True
    size = (700, 400)
    model_type = TransferOrder
    report_class = TransferOrderReceipt
    gladefile = "TransferOrderDetails"
    proxy_widgets = ('open_date',
                     'receival_date',
                     'close_date_lbl',
                     'source_branch_name',
                     'destination_branch_name',
                     'source_responsible_name',
                     'destination_responsible_name',
                     'invoice_number',
                     'comments')

    def __init__(self, store, model):
        BaseEditor.__init__(self, store, model)
        self._setup_widgets()

    def _setup_status(self):
        self.status.set_text(self.model.status_str)

        local_branch = api.get_current_branch(self.store)
        sent_remote_order = (self.model.status == self.model.STATUS_SENT and
                             self.model.destination_branch == local_branch)

        if not sent_remote_order:
            self.receive_button.hide()
        else:
            self.cancel_button.hide()
        if self.model.status == self.model.STATUS_RECEIVED:
            self.close_date_lbl.set_label(_(u"Receival date:"))
            self.cancel_button.hide()
        if self.model.status == self.model.STATUS_CANCELLED:
            self.close_date_lbl.set_label(_(u"Cancel date:"))
            self.cancel_button.hide()

    def _setup_widgets(self):
        self._setup_status()

        self.product_list.set_columns(self._get_product_columns())
        products = self.store.find(TransferOrderItem, transfer_order=self.model)
        self.product_list.add_list(list(products))

        value_format = '<b>%s</b>'
        total_label = value_format % api.escape(_("Total:"))
        products_summary_label = SummaryLabel(klist=self.product_list,
                                              column='total',
                                              label=total_label,
                                              value_format=value_format)
        products_summary_label.show()
        self.products_vbox.pack_start(products_summary_label, False)

    def _get_product_columns(self):
        return [Column("sellable.code", title=_("Code"), data_type=str,
                       justify=gtk.JUSTIFY_RIGHT, width=130),
                Column("sellable.description", title=_("Description"),
                       data_type=str, expand=True),
                Column("quantity", title=_("Quantity"),
                       data_type=int, justify=gtk.JUSTIFY_RIGHT),
                Column("sellable.cost", title=_("Cost"), width=100,
                       data_type=currency, justify=gtk.JUSTIFY_RIGHT),
                Column("total", title=_(u"Total Cost"), width=100,
                       data_type=currency, justify=gtk.JUSTIFY_RIGHT)]

    #
    # BaseEditor Hooks
    #

    def setup_proxies(self):
        if self.model.status == TransferOrder.STATUS_CANCELLED:
            self.receival_date.set_property('model-attribute', 'cancel_date')
        elif self.model.status == TransferOrder.STATUS_RECEIVED:
            self.receival_date.set_property('model-attribute', 'receival_date')
        self.proxy = self.add_proxy(self.model, self.proxy_widgets)

    def on_receive_button__clicked(self, event):
        assert self.model.status == self.model.STATUS_SENT

        if yesno(_(u'Receive the order?'), gtk.RESPONSE_YES, _(u'Receive'),
                 _(u"Don't receive")):
            responsible = api.get_current_user(self.store).person.employee
            self.model.receive(responsible)
            self.store.commit(close=False)
            self.receival_date.set_property('model-attribute', 'receival_date')
            self.proxy.update_many(['destination_responsible_name',
                                    'receival_date'])

        self._setup_status()

    def on_cancel_button__clicked(self, event):
        if yesno(_(u'Cancel the order?'), gtk.RESPONSE_YES, _(u'Cancel transfer'),
                 _(u"Don't cancel")):
            responsible = api.get_current_user(self.store).person.employee
            self.model.cancel(responsible)
            self.store.commit(close=False)
            self.receival_date.set_property('model-attribute', 'cancel_date')
            self.proxy.update_many(['destination_responsible_name',
                                    'receival_date'])
        self.setup_proxies()
        self._setup_status()
    #
    # Callbacks
    #

    def on_print_button__clicked(self, button):
        print_report(self.report_class, self.model)
