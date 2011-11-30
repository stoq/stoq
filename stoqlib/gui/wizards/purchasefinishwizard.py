# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2009 Async Open Source <http://www.async.com.br>
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
"""Purchase Finish Wizard"""

import datetime

import gtk
import pango

from kiwi.datatypes import currency
from kiwi.ui.widgets.list import Column, ColoredColumn, SummaryLabel
from kiwi.python import Settable

from stoqlib.domain.interfaces import IInPayment
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.payment.operation import register_payment_operations
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.purchase import PurchaseOrder, PurchaseItemView
from stoqlib.lib.defaults import payment_value_colorize
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.formatters import format_quantity
from stoqlib.gui.base.wizards import WizardEditorStep, BaseWizard
from stoqlib.gui.wizards.purchasewizard import PurchasePaymentStep

_ = stoqlib_gettext


#
# Wizard Steps
#


class PurchaseFinishProductListStep(WizardEditorStep):
    gladefile = 'PurchaseFinishProductListStep'
    model_type = Settable
    proxy_widgets = ()

    def __init__(self, conn, wizard, model):
        WizardEditorStep.__init__(self, conn, wizard, model)
        self._setup_widgets()

    def _setup_widgets(self):
        self.product_list.set_columns(self._get_columns())
        items = PurchaseItemView.select_by_purchase(self.model.purchase,
                                                    self.conn)
        self.product_list.add_list(items)

        self._setup_summary()

    def _setup_summary(self):
        self.summary = SummaryLabel(klist=self.product_list,
                                    column='total_received',
                                    value_format='<b>%s</b>')
        self.summary.show()
        self.vbox1.pack_start(self.summary, expand=False)

    def _get_columns(self):
        return [Column('description', title=_('Description'),
                       data_type=str, expand=True, searchable=True),
                Column('quantity', title=_('Ordered'), data_type=int,
                       width=90, format_func=format_quantity, expand=True),
                Column('quantity_received', title=_('Received'), data_type=int,
                       width=110, format_func=format_quantity),
                Column('sellable.unit_description', title=_('Unit'),
                       data_type=str, width=50),
                Column('cost', title=_('Cost'), data_type=currency, width=90),
                Column('total_received', title=_('Total'), data_type=currency,
                       width=100)]

    #
    # WizardStep hooks
    #

    def next_step(self):
        return PurchaseFinishPaymentAdjustStep(self.conn, self.wizard,
                                               self.model, self)

    def has_previous_step(self):
        return False


class PurchaseFinishPaymentAdjustStep(WizardEditorStep):
    gladefile = 'PurchaseFinishPaymentAdjustStep'
    model_type = Settable
    proxy_widgets = ('received_value', 'paid_value', 'missing_value')

    def _setup_widgets(self):
        self.received_value.set_bold(True)
        self.paid_value.set_bold(True)
        self.missing_value.set_bold(True)

        self.payment_list.set_columns(self._get_columns())
        items = self.model.purchase.payments
        self.payment_list.add_list(items)

        if self.model.paid_value > self.model.received_value:
            self.model.missing_value = currency(abs(self.model.missing_value))
            self.missing_label.set_label(_('Overpaid:'))

    def _get_columns(self):
        return [Column('id', "#", data_type=int, width=50,
                       format='%04d', justify=gtk.JUSTIFY_RIGHT),
                Column('description', _("Description"), data_type=str,
                       width=150, expand=True,
                       ellipsize=pango.ELLIPSIZE_END),
                Column('due_date', _("Due date"), sorted=True,
                       data_type=datetime.date, width=90,
                       justify=gtk.JUSTIFY_RIGHT),
                Column('paid_date', _("Paid date"),
                      data_type=datetime.date, width=90),
                Column('status_str', _("Status"), data_type=str, width=80),
                ColoredColumn('value', _("Value"), data_type=currency,
                              width=90, color='red',
                              justify=gtk.JUSTIFY_RIGHT,
                              data_func=payment_value_colorize),
                ColoredColumn('paid_value', _("Paid value"),
                              data_type=currency, width=92, color='red',
                              justify=gtk.JUSTIFY_RIGHT,
                              data_func=payment_value_colorize)]

    def _clear_not_paid(self):
        payments = Payment.selectBy(status=Payment.STATUS_PENDING,
                                    group=self.model.purchase.group,
                                    connection=self.conn)
        for payment in payments:
            payment.cancel()

    def _cancel_not_received_items(self):
        items = self.model.purchase.get_pending_items()
        for item in items:
            item.quantity = item.quantity_received

    #
    # WizardStep hooks
    #

    def has_next_step(self):
        # If we received more than we have already paid,
        # new payments need to be created
        if self.model.paid_value < self.model.received_value:
            return True

        # Else, just one incoming payment will be created.
        return False

    def next_step(self):
        return PurchaseFinishPaymentStep(self.wizard, self, self.conn,
                                         self.model)

    def setup_proxies(self):
        self._clear_not_paid()
        self._cancel_not_received_items()
        self._setup_widgets()
        self.proxy = self.add_proxy(self.model, self.proxy_widgets)


class PurchaseFinishPaymentStep(PurchasePaymentStep):

    def __init__(self, wizard, previous, conn, model):
        PurchasePaymentStep.__init__(self, wizard, previous, conn,
                                     model.purchase, model.missing_value)

    def has_next_step(self):
        return False

#
# Main wizard
#


class PurchaseFinishWizard(BaseWizard):
    size = (775, 400)
    title = _('Purchase Finish')

    def __init__(self, conn, purchase):
        self.purchase = purchase
        model = self._create_model(purchase)

        if self.purchase.status != PurchaseOrder.ORDER_CONFIRMED:
            raise ValueError('Invalid order status. It should '
                             'be ORDER_CONFIRMED')

        register_payment_operations()
        first_step = PurchaseFinishProductListStep(conn, self, model)
        BaseWizard.__init__(self, conn, first_step, model)

    def _create_model(self, purchase):
        paid_value = currency(purchase.payments.sum('paid_value') or 0)
        received_value = purchase.get_received_total()
        return Settable(received_value=received_value,
                        paid_value=paid_value,
                        missing_value=currency(received_value - paid_value),
                        purchase=purchase)

    def _confirm_new_payments(self):
        payments = Payment.selectBy(
            connection=self.conn,
            status=Payment.STATUS_PREVIEW,
            group=self.purchase.group)

        for payment in payments:
            payment.set_pending()

    def _create_return_payment(self):
        money = PaymentMethod.get_by_name(self.conn, 'money')
        description = _('Return payment for order %s' % self.purchase.id)
        value = currency(self.model.paid_value - self.model.received_value)
        today = datetime.date.today()

        payment = Payment(open_date=today,
                          description=description,
                          value=value,
                          base_value=value,
                          due_date=today,
                          method=money,
                          group=self.purchase.group,
                          till=None,
                          category=None,
                          connection=self.conn)
        payment.set_pending()
        payment.addFacet(IInPayment, connection=self.conn)

    def finish(self):
        model = self.model
        self.retval = model

        if model.paid_value < model.received_value:
            self._confirm_new_payments()
        else:
            self._create_return_payment()
        self.purchase.close()

        self.close()
