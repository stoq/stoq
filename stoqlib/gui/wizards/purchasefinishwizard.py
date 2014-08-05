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

from kiwi.currency import currency
from kiwi.ui.objectlist import Column, ColoredColumn, SummaryLabel
from kiwi.python import Settable

from stoqlib.api import api
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.purchase import PurchaseOrder, PurchaseItemView
from stoqlib.lib.dateutils import localtoday
from stoqlib.lib.defaults import payment_value_colorize
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.formatters import format_quantity
from stoqlib.gui.base.wizards import WizardEditorStep, BaseWizard
from stoqlib.gui.search.searchcolumns import IdentifierColumn
from stoqlib.gui.wizards.purchasewizard import PurchasePaymentStep

_ = stoqlib_gettext


#
# Wizard Steps
#


class PurchaseFinishProductListStep(WizardEditorStep):
    gladefile = 'PurchaseFinishProductListStep'
    model_type = Settable
    proxy_widgets = ()

    def __init__(self, store, wizard, model):
        WizardEditorStep.__init__(self, store, wizard, model)
        self._setup_widgets()

    def _setup_widgets(self):
        self.product_list.set_columns(self._get_columns())
        items = PurchaseItemView.find_by_purchase(self.store, self.model.purchase)
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
        return PurchaseFinishPaymentAdjustStep(self.store, self.wizard,
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
        return [IdentifierColumn('identifier', title=_('Purchase #')),
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
        payments = self.store.find(Payment, status=Payment.STATUS_PENDING,
                                   group=self.model.purchase.group)
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
        return PurchaseFinishPaymentStep(self.wizard, self, self.store,
                                         self.model)

    def setup_proxies(self):
        self._clear_not_paid()
        self._cancel_not_received_items()
        self._setup_widgets()
        self.proxy = self.add_proxy(self.model, self.proxy_widgets)


class PurchaseFinishPaymentStep(PurchasePaymentStep):

    def __init__(self, wizard, previous, store, model):
        PurchasePaymentStep.__init__(self, wizard, previous, store,
                                     model.purchase, model.missing_value)

    def has_next_step(self):
        return False

#
# Main wizard
#


class PurchaseFinishWizard(BaseWizard):
    size = (775, 400)
    title = _('Purchase Finish')

    def __init__(self, store, purchase):
        sync_mode = api.sysparam.get_bool('SYNCHRONIZED_MODE')
        # When in sync mode, only the branch owner can finish a purchase order.
        if sync_mode:
            assert purchase.branch == api.get_current_branch(store)

        self.purchase = purchase
        model = self._create_model(purchase)

        if self.purchase.status != PurchaseOrder.ORDER_CONFIRMED:
            raise ValueError('Invalid order status. It should '
                             'be ORDER_CONFIRMED')

        first_step = PurchaseFinishProductListStep(store, self, model)
        BaseWizard.__init__(self, store, first_step, model)

    def _create_model(self, purchase):
        paid_value = currency(purchase.payments.sum(Payment.paid_value) or 0)
        received_value = purchase.received_total
        return Settable(received_value=received_value,
                        paid_value=paid_value,
                        missing_value=currency(received_value - paid_value),
                        purchase=purchase)

    def _confirm_new_payments(self):
        payments = self.store.find(Payment,
                                   status=Payment.STATUS_PREVIEW,
                                   group=self.purchase.group)

        for payment in payments:
            payment.set_pending()
            yield payment

    def _create_return_payment(self):
        money = PaymentMethod.get_by_name(self.store, u'money')
        description = _(u'Money returned for order %s') % (
            self.purchase.identifier, )
        value = currency(self.model.paid_value - self.model.received_value)
        today = localtoday().date()

        payment = Payment(open_date=today,
                          branch=self.purchase.branch,
                          description=description,
                          value=value,
                          base_value=value,
                          due_date=today,
                          method=money,
                          group=self.purchase.group,
                          category=None,
                          store=self.store,
                          payment_type=Payment.TYPE_IN)
        payment.set_pending()
        return payment

    def is_for_another_branch(self):
        return False

    def finish(self):
        """  When finishing this wizard is necessary to check if the paid
        value was less or more than the received value.
        If the paid value was lesser than what was received is created
        a new payment. Otherwise a return payment is created for the purchase.
        """
        model = self.model

        if model.paid_value < model.received_value:
            self.retval = self._confirm_new_payments()
        else:
            self.retval = self._create_return_payment()
        self.purchase.close()

        self.close()
