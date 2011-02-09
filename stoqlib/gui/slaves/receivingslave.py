# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005, 2009 Async Open Source <http://www.async.com.br>
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

from kiwi.datatypes import ValidationError, ValueUnset

from stoqlib.domain.fiscal import CfopData
from stoqlib.domain.receiving import ReceivingOrder
from stoqlib.domain.person import PersonAdaptToTransporter
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.editors.baseeditor import BaseEditorSlave
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.editors.noteeditor import NoteEditor

_ = stoqlib_gettext


class ReceivingInvoiceSlave(BaseEditorSlave):

    model_type = ReceivingOrder
    gladefile = 'ReceivingInvoiceSlave'
    proxy_widgets = ('transporter',
                     'responsible_name',
                     'products_total',
                     'freight_combo',
                     'freight',
                     'ipi',
                     'cfop',
                     'branch',
                     'supplier_label',
                     'order_number',
                     'total',
                     'invoice_number',
                     'icms_total',
                     'discount_value',
                     'secure_value',
                     'expense_value')

    def __init__(self, conn, model=None, visual_mode=False):
        self.proxy = None
        BaseEditorSlave.__init__(self, conn, model, visual_mode)

    #
    # BaseEditorSlave hooks
    #

    def _setup_transporter_entry(self):
        # FIXME: Implement and use IDescribable on PersonAdaptToTransporter
        table = PersonAdaptToTransporter
        transporters = table.get_active_transporters(self.conn)
        items = [(t.person.name, t) for t in transporters]
        self.transporter.prefill(items)

        # The user should not be allowed to change the transporter,
        # if it's already set.
        if self.model.transporter:
            self.transporter.set_sensitive(False)

    def _setup_widgets(self):
        self.total.set_bold(True)

        purchase = self.model.purchase
        if not purchase:
            for widget in (self.purchase_number_label,
                           self.purchase_supplier_label,
                           self.order_number, self.supplier_label):
                widget.hide()
        elif purchase and purchase.is_paid():
            for widget in (self.ipi, self.discount_value, self.icms_total,
                           self.secure_value, self.expense_value):
                widget.set_sensitive(False)

        # Transporter entry setup
        self._setup_transporter_entry()

        # CFOP entry setup
        cfop_items = [(item.get_description(), item)
                      for item in CfopData.select(connection=self.conn)]
        self.cfop.prefill(cfop_items)
        
        # Freight combo setup
        freight_items = [(self.model.freight_types[item], item)
                 for item in self.model.get_freight_types()]
        self.freight_combo.prefill(freight_items)

    def create_freight_payment(self):
        """Tells if we should create a separate payment for freight or not
        
        It should return True or False. If True is returned, a separate payment
        will be created for freight. If not, it'll be included on installments.
        """
        freight_type = self.freight_combo.read()
        if freight_type == self.model.FREIGHT_FOB_PAYMENT:
            return True
        return False

    #
    # BaseEditorSlave hooks
    #

    def update_visual_mode(self):
        self.notes_button.hide()
        self.freight_combo.set_sensitive(False)

    def setup_proxies(self):
        self._setup_widgets()
        self.proxy = self.add_proxy(self.model,
                                    ReceivingInvoiceSlave.proxy_widgets)

        self.model.invoice_total = self.model.get_products_total()

        purchase = self.model.purchase
        if purchase:
            if not self.visual_mode:
                # These values are duplicates from the purchase. If we are
                # visualising the order, the value should be it's own, not the
                # purchase ones.
                self.model.freight_type = \
                        self.model.get_freight_type_adapted_from_payment()
                self.proxy.update('freight_type')
                self.model.freight_total = purchase.expected_freight
                self.proxy.update('freight_total')
            self.model.supplier = purchase.supplier
            self.model.transporter = purchase.transporter
            self.proxy.update('transporter')

        self.proxy.update('total')

    #
    # Callbacks
    #

    def _positive_validator(self, widget, value):
        if value < 0:
            return ValidationError(_("This field cannot be negative"))

    on_freight__validate = _positive_validator
    on_ipi__validate = _positive_validator
    on_icms_total__validate = _positive_validator
    on_secure_value__validate = _positive_validator
    on_expense_value__validate = _positive_validator

    def on_notes_button__clicked(self, *args):
        run_dialog(NoteEditor, self, self.conn, self.model, 'notes',
                   title=_('Additional Information'))

    def on_invoice_number__validate(self, widget, value):
        if value < 1 or value > 999999:
            return ValidationError(_("Receving order number must be "
                                     "between 1 and 999999"))

        order_count = ReceivingOrder.selectBy(invoice_number=value,
                                              supplier=self.model.supplier,
                                              connection=self.conn).count()
        if order_count > 0:
            supplier_name = self.model.supplier.person.name
            return ValidationError(_(u'Invoice %d already exists for '
                                     'supplier %s.' % (value, supplier_name,)))

    def on_freight_combo__validate(self, widget, value):
        if (not self.visual_mode and
            self.model.purchase.is_paid() and
            value == self.FREIGHT_FOB_INSTALLMENTS):
            return ValidationError(_(u'Cannot include freight value on '
                                      'an already paid purchase. Select '
                                      'another freight type.'))


    def after_freight_combo__content_changed(self, widget):
        value = widget.read()

        if value == self.model.FREIGHT_CIF_UNKNOWN:
            self.freight.set_sensitive(False)
            self.model.freight_total = 0
            if self.proxy:
                self.proxy.update('freight_total')
        else:
            if not self.visual_mode:
                self.freight.set_sensitive(True)

        if self.proxy:
            self.proxy.update('total')

    def after_freight__content_changed(self, widget):
        try:
            value = widget.read()
        except ValidationError:
            value = ValueUnset

        if value is ValueUnset:
            self.model.freight_total = 0
        self.proxy.update('total')

    def after_ipi__content_changed(self, widget):
        try:
            value = widget.read()
        except ValidationError:
            value = ValueUnset

        if value is ValueUnset:
            self.model.ipi_total = 0
        self.proxy.update('total')

    def after_discount_value__content_changed(self, widget):
        try:
            value = widget.read()
        except ValidationError:
            value = ValueUnset

        if value is ValueUnset:
            self.model.discount_value = 0
        self.proxy.update('total')

    def after_discount_value__validate(self, widget, value):
        if value < 0:
            return ValidationError(_("Discount must be greater than zero"))
        if value > self.model.get_total():
            return ValidationError(_("Discount must be less "
                                     "than %s" % (self.model.get_total(),)))

    def after_secure_value__content_changed(self, widget):
        try:
            value = widget.read()
        except ValidationError:
            value = ValueUnset

        if value is ValueUnset:
            self.model.secure_value = 0
        self.proxy.update('total')

    def after_expense_value__content_changed(self, widget):
        try:
            value = widget.read()
        except ValidationError:
            value = ValueUnset

        if value is ValueUnset:
            self.model.expense_value = 0
        self.proxy.update('total')
