# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2007 Async Open Source <http://www.async.com.br>
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
""" Sale return wizards definition """

import decimal
import sys

import gtk
from kiwi.currency import currency
from kiwi.datatypes import ValidationError, converter
from kiwi.ui.objectlist import Column

from stoqlib.api import api
from stoqlib.domain.returned_sale import ReturnedSale, ReturnedSaleItem
from stoqlib.lib.formatters import format_quantity
from stoqlib.lib.message import info
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.base.wizards import WizardEditorStep, BaseWizard
from stoqlib.gui.slaves.paymentslave import (register_payment_slaves,
                                             MultipleMethodSlave)
from stoqlib.gui.wizards.abstractwizard import SellableItemStep


_ = stoqlib_gettext


class SaleReturnItemsStep(SellableItemStep):
    model_type = ReturnedSale
    item_table = ReturnedSaleItem
    summary_label_text = '<b>%s</b>' % api.escape(_("Total to return:"))

    #
    #  SellableItemStep
    #

    def post_init(self):
        super(SaleReturnItemsStep, self).post_init()

        self.hide_item_addition_toolbar()
        self.hide_add_button()
        self.hide_edit_button()
        self.hide_del_button()

        self.slave.klist.connect('cell-edited', self._on_klist__cell_edited)
        self.slave.klist.connect('cell-editing-started',
                                 self._on_klist__cell_editing_started)
        self.force_validation()

    def next_step(self):
        return SaleReturnInvoiceStep(self.conn, self.wizard,
                                     model=self.model, previous=self)

    def get_columns(self):
        adjustment = gtk.Adjustment(lower=0, upper=sys.maxint,
                                    step_incr=1)
        return [
            Column('will_return', title=_('Return'),
                   data_type=bool, editable=True),
            Column('sellable.description', title=_('Description'),
                   data_type=str, expand=True),
            Column('sale_price', title=_('Sale price'),
                   data_type=currency),
            Column('max_quantity', title=_('Sold quantity'),
                   data_type=decimal.Decimal, format_func=format_quantity),
            Column('quantity', title=_('Quantity'),
                   data_type=decimal.Decimal, format_func=format_quantity,
                   spin_adjustment=adjustment, editable=True),
            Column('total', title=_('Total'),
                   data_type=currency),
            ]

    def get_saved_items(self):
        return self.model.returned_items

    def validate_step(self):
        returned_items = [item for item in
                          self.model.returned_items if item.will_return]

        if not len(returned_items):
            info(_("You need to have at least one item to return"))
            return False
        if not all([0 < item.quantity <= item.max_quantity for
                    item in returned_items]):
            # Just a precaution..should not happen!
            return False

        return True

    def validate(self, value):
        self.wizard.refresh_next(value and self.validate_step())

    #
    #  Callbacks
    #

    def _on_klist__cell_edited(self, klist, obj, attr):
        if attr == 'quantity':
            # FIXME: Even with the adjustment, the user still can type
            # values out of range with the keyboard. Maybe it's kiwi's fault
            if obj.quantity > obj.max_quantity:
                obj.quantity = obj.max_quantity
            if obj.quantity < 0:
                obj.quantity = 0
            # Changing quantity from anything to 0 will uncheck will_return
            # Changing quantity from 0 to anything will check will_return
            obj.will_return = bool(obj.quantity)
        elif attr == 'will_return':
            # Unchecking will_return will make quantity goes to 0
            if not obj.will_return:
                obj.quantity = 0

        self.summary.update_total()
        self.force_validation()

    def _on_klist__cell_editing_started(self, klist, obj, attr,
                                        renderer, editable):
        if attr == 'quantity':
            adjustment = editable.get_adjustment()
            # Don't let the user return more than was bought
            adjustment.set_upper(obj.max_quantity)


class SaleReturnInvoiceStep(WizardEditorStep):
    gladefile = 'SaleReturnInvoiceStep'
    model_type = ReturnedSale
    proxy_widgets = [
        'responsible',
        'invoice_number',
        'reason',
        'sale_total',
        'paid_total',
        'returned_total',
        'total_amount_abs',
        ]

    #
    #  WizardEditorStep
    #

    def post_init(self):
        self.register_validate_function(self.wizard.refresh_next)
        self.force_validation()
        self._update_widgets()

    def next_step(self):
        return SaleReturnPaymentStep(self.conn, self.wizard,
                                     model=self.model, previous=self)

    def has_next_step(self):
        return self.model.total_amount > 0

    def setup_proxies(self):
        self.proxy = self.add_proxy(self.model, self.proxy_widgets)

    #
    #  Private
    #

    def _update_widgets(self):
        self.proxy.update('total_amount_abs')

        if self.model.total_amount < 0:
            self.total_amount_lbl.set_text(_("Overpaid:"))
        elif self.model.total_amount > 0:
            self.total_amount_lbl.set_text(_("Missing:"))
        else:
            self.total_amount_lbl.set_text(_("Difference:"))

        self.wizard.update_view()
        self.force_validation()

    #
    #  Callbacks
    #

    def on_invoice_number__validate(self, widget, value):
        if not 0 < value <= 999999999:
            return ValidationError(_("Invoice number must be between "
                                     "1 and 999999999"))
        if self.model.check_unique_value_exists('invoice_number', value):
            return ValidationError(_("Invoice number already exists."))


class SaleReturnPaymentStep(WizardEditorStep):
    gladefile = 'HolderTemplate'
    model_type = ReturnedSale

    #
    #  WizardEditorStep
    #

    def post_init(self):
        self.register_validate_function(self._validation_func)
        self.force_validation()

        before_debt = currency(self.model.sale_total - self.model.paid_total)
        now_debt = currency(before_debt - self.model.returned_total)
        info(_("The client's debt has changed. "
               "Use this step to adjust the payments."),
             _("The debt before was %s and now is %s. Cancel some unpaid "
               "installments and create new ones.") % (
             converter.as_string(currency, before_debt),
             converter.as_string(currency, now_debt)))

    def setup_slaves(self):
        register_payment_slaves()
        outstanding_value = (self.model.total_amount_abs +
                             self.model.paid_total)
        self.slave = MultipleMethodSlave(self.wizard, self, self.conn,
                                         self.model, None,
                                         outstanding_value=outstanding_value,
                                         finish_on_total=False,
                                         allow_remove_paid=False)
        self.slave.enable_remove()
        self.attach_slave('place_holder', self.slave)

    def validate_step(self):
        return True

    def has_next_step(self):
        return False

    #
    #  Callbacks
    #

    def _validation_func(self, value):
        can_finish = value and self.slave.can_confirm()
        self.wizard.refresh_next(can_finish)


class SaleReturnWizard(BaseWizard):
    size = (600, 350)
    title = _('Return Sale Order')

    def __init__(self, conn, model):
        assert isinstance(model, ReturnedSale)

        for returned_item in model.returned_items:
            # Some temporary attributes
            returned_item.will_return = bool(returned_item.quantity)
            returned_item.max_quantity = returned_item.quantity

        first_step = SaleReturnItemsStep(self, None, conn, model)
        BaseWizard.__init__(self, conn, first_step, model)

    #
    #  BaseWizard
    #

    def finish(self):
        for payment in self.model.group.payments:
            if payment.is_preview():
                # Set payments created on SaleReturnPaymentStep as pending
                payment.set_pending()

        self.model.return_()
        self.retval = True
        self.close()
