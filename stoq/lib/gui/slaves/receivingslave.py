# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005, 2014 Async Open Source <http://www.async.com.br>
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
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##
##
""" Purchase receiving slaves implementation"""

from kiwi.currency import currency
from kiwi.datatypes import ValidationError, ValueUnset
from kiwi.utils import gsignal
from storm.exceptions import NotOneError

from stoqlib.api import api
from stoqlib.domain.fiscal import CfopData
from stoqlib.domain.receiving import ReceivingInvoice
from stoqlib.domain.person import Transporter
from stoqlib.lib.translation import stoqlib_gettext
from stoq.lib.gui.editors.baseeditor import BaseEditorSlave
from stoq.lib.gui.base.dialogs import run_dialog
from stoq.lib.gui.editors.noteeditor import NoteEditor
from stoqlib.lib.validators import validate_invoice_key

_ = stoqlib_gettext


class ReceivingInvoiceSlave(BaseEditorSlave):

    model_type = ReceivingInvoice
    gladefile = 'ReceivingInvoiceSlave'
    receiving_widgets = ['cfop']
    invoice_widgets = ['transporter',
                       'branch',
                       'responsible_name',
                       'freight_combo',
                       'freight',
                       'ipi',
                       'total',
                       'products_total',
                       'supplier_label',
                       'invoice_number',
                       'invoice_key',
                       'icms_total',
                       'icms_st_total',
                       'discount_value',
                       'secure_value',
                       'expense_value']
    proxy_widgets = receiving_widgets + invoice_widgets

    gsignal('activate')

    def __init__(self, store, model, visual_mode=False):
        self.purchases = list(model.get_purchase_orders())

        # Save the receiving order if there is only one for this receiving invoice
        try:
            self._receiving_order = model.receiving_orders.one()
        except NotOneError:
            self._receiving_order = None
        BaseEditorSlave.__init__(self, store, model, visual_mode)

    #
    # BaseEditorSlave hooks
    #

    def _get_receiving_items(self):
        items = []
        for receiving in self.model.receiving_orders:
            for item in receiving.get_items(with_children=False):
                items.append(item)
        return items

    def _setup_transporter_entry(self):
        transporters = Transporter.get_active_transporters(self.store)
        self.transporter.prefill(api.for_combo(transporters))

    def _setup_freight_combo(self):
        freight_items = [(value, key) for (key, value) in
                         ReceivingInvoice.freight_types.items()]

        # If there is at least one purchase with pending payments, than we can
        # change those.
        payments = self._receiving_order and self._receiving_order.payments
        can_change_installments = not payments or any(not p.is_paid() for p in payments)
        if not can_change_installments and not self.visual_mode:
            ri = ReceivingInvoice
            freight_items.remove((ri.freight_types[ri.FREIGHT_FOB_INSTALLMENTS],
                                  ri.FREIGHT_FOB_INSTALLMENTS))

        # Disconnect that callback to prevent an AttributeError
        # caused by the lack of a proxy.
        handler_func = self.after_freight_combo__content_changed
        self.freight_combo.handler_block_by_func(handler_func)
        self.freight_combo.prefill(freight_items)
        self.freight_combo.handler_unblock_by_func(handler_func)

    def _setup_widgets(self):
        self.total.set_bold(True)
        idents = sorted(p.identifier for p in self.purchases)
        identifier = ', '.join(str(i) for i in idents)
        self.identifier.set_text(identifier)

        # TODO: Testar isso quando compras > 1
        if len(self.purchases) == 1 and self.purchases[0].is_paid():
            # This widgets would make the value of the installments change.
            for widget in (self.ipi, self.discount_value, self.icms_total,
                           self.icms_st_total, self.secure_value, self.expense_value):
                widget.set_sensitive(False)

        # Only allow to edit the cfop if there is only one receiving for this invoice
        self.cfop.set_sensitive(bool(not self.visual_mode and self._receiving_order))

        self._setup_transporter_entry()
        self._setup_freight_combo()

        cfops = CfopData.get_for_receival(self.store)
        self.cfop.prefill(api.for_combo(cfops))
        self.table.set_focus_chain([self.invoice_hbox,
                                    self.invoice_key,
                                    self.cfop,
                                    self.transporter,
                                    self.freight_combo,
                                    self.notes_box,
                                    self.freight,
                                    self.ipi,
                                    self.icms_total,
                                    self.icms_st_total,
                                    self.discount_value,
                                    self.secure_value,
                                    self.expense_value])

    def create_freight_payment(self):
        """Tells if we should create a separate payment for freight or not

        It should return True or False. If True is returned, a separate payment
        will be created for freight. If not, it'll be included on installments.
        """
        freight_type = self.freight_combo.read()
        return freight_type == ReceivingInvoice.FREIGHT_FOB_PAYMENT

    #
    # BaseEditorSlave hooks
    #

    def update_visual_mode(self):
        self.observations_button.hide()
        self.freight_combo.set_sensitive(False)

    def setup_proxies(self):
        self.receiving_proxy = None
        self.invoice_proxy = None
        self._setup_widgets()
        self.invoice_proxy = self.add_proxy(self.model,
                                            ReceivingInvoiceSlave.invoice_widgets)
        receiving_order = self._receiving_order or self.model.receiving_orders.any()
        self.receiving_proxy = self.add_proxy(receiving_order, self.receiving_widgets)

        self.model.invoice_total = self.model.products_total

        if len(self.purchases) == 1:
            purchase = self.purchases[0]
            if not self.visual_mode:
                # These values are duplicates from the purchase. If we are
                # visualising the order, the value should be it's own, not the
                # purchase ones.
                self.freight_combo.update(self.model.guess_freight_type())
                self.freight.update(purchase.expected_freight)

            self.model.supplier = purchase.supplier
            self.transporter.update(purchase.transporter)

        # Prefill the IPI and ICMS ST totals based on the sum of the itens values
        receiving_items = self._get_receiving_items()
        ipi_total = icms_st_total = currency(0)
        for item in receiving_items:
            ipi_total += item.ipi_value or 0
            icms_st_total += item.icms_st_value or 0

        self.ipi.update(ipi_total)
        self.icms_st_total.update(icms_st_total)

        self.invoice_proxy.update('total')

    def on_invoice_number__activate(self, widget):
        self.emit('activate')

    def on_freight__activate(self, widget):
        self.emit('activate')

    def on_ipi__activate(self, widget):
        self.emit('activate')

    def on_icms_total__activate(self, widget):
        self.emit('activate')

    def on_icms_st_total__activate(self, widget):
        self.emit('activate')

    def on_discount_value__activate(self, widget):
        self.emit('activate')

    def on_secure_value__activate(self, widget):
        self.emit('activate')

    def on_expense_value__activate(self, widget):
        self.emit('activate')

    def _positive_validator(self, widget, value):
        if value < 0:
            return ValidationError(_("This field cannot be negative"))

    on_freight__validate = _positive_validator
    on_ipi__validate = _positive_validator
    on_icms_total__validate = _positive_validator
    on_secure_value__validate = _positive_validator
    on_expense_value__validate = _positive_validator

    def on_observations_button__clicked(self, *args):
        run_dialog(NoteEditor, self, self.store, self.model, 'notes',
                   title=_('Additional Information'))

    def on_invoice_number__validate(self, widget, value):
        if self.visual_mode:
            return

        if not 0 < value <= 999999999:
            return ValidationError(
                _("Invoice number must be between 1 and 999999999"))

        with api.new_store() as store:
            # Using a transaction to do the verification bellow because,
            # if we use self.store the changes on the invoice will be
            # saved at the same time in the database and it'll think
            # some valid invoices are invalid.
            is_valid = ReceivingInvoice.check_unique_invoice_number(
                store, value, self.model.supplier)
        if not is_valid:
            supplier_name = self.model.supplier.person.name
            return ValidationError(_(u'Invoice %d already exists for '
                                     'supplier %s.') % (value, supplier_name, ))

    def after_freight_combo__content_changed(self, widget):
        value = widget.read()

        if value == ReceivingInvoice.FREIGHT_CIF_UNKNOWN:
            self.freight.update(0)
            self.freight.set_sensitive(False)
        else:
            if not self.visual_mode:
                self.freight.set_sensitive(True)
                if (not self.model.freight_total and
                        value in ReceivingInvoice.FOB_FREIGHTS):
                    # Restore the freight value to the purchase expected one.
                    self.freight.update(self.purchases[0].expected_freight)

        if self.invoice_proxy is not None:
            self.invoice_proxy.update('total')

    def after_freight__content_changed(self, widget):
        self.handle_entry_content_changed(widget, 'freight_total')

    def after_ipi__content_changed(self, widget):
        self.handle_entry_content_changed(widget, 'ipi_total')

    def after_icms_st_total__content_changed(self, widget):
        self.handle_entry_content_changed(widget, 'icms_st_total')

    def after_discount_value__content_changed(self, widget):
        self.handle_entry_content_changed(widget, 'discount_value')

    def after_discount_value__validate(self, widget, value):
        if value < 0:
            return ValidationError(_("Discount must be greater than zero"))
        if value > self.model.total:
            return ValidationError(_("Discount must be less "
                                     "than %s") % (self.model.total,))

    def after_secure_value__content_changed(self, widget):
        self.handle_entry_content_changed(widget, 'secure_value')

    def after_expense_value__content_changed(self, widget):
        self.handle_entry_content_changed(widget, 'expense_value')

    def handle_entry_content_changed(self, widget, attr):
        try:
            value = widget.read()
        except ValidationError:
            value = ValueUnset

        if value is ValueUnset:
            setattr(self.model, attr, 0)

        if self.invoice_proxy is not None:
            self.invoice_proxy.update('total')

    def on_invoice_key__validate(self, widget, value):
        if value and not validate_invoice_key(value):
            return ValidationError(_('Invalid key'))
