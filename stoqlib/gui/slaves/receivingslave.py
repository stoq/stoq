# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005, 2006 Async Open Source <http://www.async.com.br>
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
##  Author(s):      Evandro Vale Miquelito      <evandro@async.com.br>
##
##
""" Purchase receiving slaves implementation"""


from stoqlib.domain.fiscal import CfopData
from stoqlib.domain.receiving import ReceivingOrder
from stoqlib.domain.person import (PersonAdaptToSupplier,
                                   PersonAdaptToTransporter)
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.base.editors import BaseEditorSlave
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.editors.noteeditor import NoteEditor
from stoqlib.gui.slaves.saleslave import DiscountSurchargeSlave

_ = stoqlib_gettext


class ReceivingInvoiceSlave(BaseEditorSlave):
    model_type = ReceivingOrder
    gladefile = 'ReceivingInvoiceSlave'
    proxy_widgets = ('transporter',
                     'products_total',
                     'freight',
                     'ipi',
                     'cfop',
                     'receiving_number',
                     'branch',
                     'supplier',
                     'supplier_label',
                     'order_number',
                     'total',
                     'invoice_number',
                     'icms_total')

    #
    # BaseEditorSlave hooks
    #

    # We will avoid duplicating code like when setting up entry completions
    # on bug 2275.
    def _setup_transporter_entry(self):
        # FIXME: Implement and use IDescribable on PersonAdaptToTransporter
        table = PersonAdaptToTransporter
        transporters = table.get_active_transporters(self.conn)
        items = [(t.person.name, t) for t in transporters]
        self.transporter.prefill(items)

    def _setup_supplier_entry(self):
        # FIXME: Implement and use IDescribable on PersonAdaptToSupplier
        table = PersonAdaptToSupplier
        suppliers = table.get_active_suppliers(self.conn)
        items = [(s.person.name, s) for s in suppliers]
        self.supplier.prefill(items)

    def _setup_widgets(self):
        purchase_widgets = (self.purchase_details_label,
                            self.purchase_number_label,
                            self.purchase_supplier_label,
                            self.order_number, self.supplier_label)
        if self.model.purchase:
            for widget in purchase_widgets:
                widget.show()
            self.receiving_supplier_label.hide()
            self.supplier.hide()
        else:
            for widget in purchase_widgets:
                widget.hide()
            self.receiving_supplier_label.show()
            self.supplier.show()
        self._setup_transporter_entry()
        self._setup_supplier_entry()
        cfop_items = [(item.get_description(), item)
                        for item in CfopData.select(connection=self.conn)]
        self.cfop.prefill(cfop_items)
        self.transporter.grab_focus()

    #
    # BaseEditorSlave hooks
    #

    def update_visual_mode(self):
        self.notes_button.hide()

    def setup_proxies(self):
        self._setup_widgets()
        self.proxy = self.add_proxy(self.model,
                                    ReceivingInvoiceSlave.proxy_widgets)
        self.model.invoice_total = self.model.get_products_total()
        self.proxy.update('total')
        purchase = self.model.purchase
        if purchase:
            transporter = purchase.transporter
            self.model.transporter = transporter
            self.proxy.update('transporter')
            self.model.supplier = purchase.supplier
            self.proxy.update('supplier')
            if purchase.freight:
                freight_value = (self.model.get_products_total() *
                                 purchase.freight / 100)
                self.model.freight_total = freight_value
                self.proxy.update('freight_total')

    def setup_slaves(self):
        slave_holder = 'discount_surcharge_holder'
        if self.get_slave(slave_holder):
            return
        self.discount_surcharge_slave = DiscountSurchargeSlave(
            self.conn, self.model, ReceivingOrder,
            visual_mode=self.visual_mode)
        self.attach_slave(slave_holder, self.discount_surcharge_slave)

    #
    # Callbacks
    #

    def on_notes_button__clicked(self, *args):
        run_dialog(NoteEditor, self, self.conn, self.model, 'notes',
                   title=_('Additional Information'))

