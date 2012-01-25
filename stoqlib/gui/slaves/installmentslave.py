# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007-2009 Async Open Source <http://www.async.com.br>
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
""" Installment confirmation slave """

import datetime

from kiwi.datatypes import currency, ValidationError
from kiwi.ui.objectlist import Column
from kiwi import ValueUnset

from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.dialogs.purchasedetails import PurchaseDetailsDialog
from stoqlib.gui.dialogs.saledetails import SaleDetailsDialog
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.parameters import sysparam
from stoqlib.domain.account import Account
from stoqlib.domain.payment.operation import register_payment_operations
from stoqlib.domain.purchase import PurchaseOrder
from stoqlib.domain.sale import Sale, SaleView

_ = stoqlib_gettext


class _ConfirmationModel(object):
    def __init__(self, payments):
        self.payments = payments
        self.close_date = datetime.date.today()

    def get_interest(self):
        return currency(sum(p.interest or 0 for p in self.payments))

    def set_interest(self, interest):
        installments = len(self.payments)
        for payment in self.payments:
            payment.interest = interest / installments

    def get_penalty(self):
        return currency(sum(p.penalty or 0 for p in self.payments))

    def set_penalty(self, penalty):
        installments = len(self.payments)
        for payment in self.payments:
            payment.penalty = penalty / installments

    def get_discount(self):
        return currency(sum(p.discount or 0 for p in self.payments))

    def set_discount(self, discount):
        installments = len(self.payments)
        for payment in self.payments:
            payment.discount = discount / installments

    def get_calculated_interest(self):
        return currency(0)

    def get_calculated_penalty(self):
        return currency(0)

    def get_installment_value(self):
        return currency(sum(p.value for p in self.payments))

    def get_total_value(self):
        return currency(self.get_installment_value() +
                        self.get_penalty() +
                        self.get_interest() -
                        self.get_discount())

    def confirm(self):
        """A hook that will be called after we pay the payments."""
        pass


class _SaleConfirmationModel(_ConfirmationModel):
    def __init__(self, payments, sale):
        if not isinstance(sale, Sale):
            raise TypeError("sale must be a Sale")
        self.pay_penalty = True
        self.pay_interest = True
        self._sale = sale
        self.open_date = self._sale.open_date.date()
        _ConfirmationModel.__init__(self, payments)

    def get_calculated_interest(self):
        return currency(sum(p.get_interest(self.close_date)
                            for p in self.payments))

    def get_calculated_penalty(self):
        return currency(sum(p.get_penalty(self.close_date)
                            for p in self.payments))

    def get_interest(self):
        if not self.pay_interest:
            return currency(0)
        return super(_SaleConfirmationModel, self).get_interest()

    def set_interest(self, interest):
        if not self.pay_interest:
            interest = currency(0)
        super(_SaleConfirmationModel, self).set_interest(interest)

    def get_penalty(self):
        if not self.pay_penalty:
            return currency(0)
        return super(_SaleConfirmationModel, self).get_penalty()

    def set_penalty(self, penalty):
        if not self.pay_penalty:
            penalty = currency(0)
        super(_SaleConfirmationModel, self).set_penalty(penalty)

    def get_order_number(self):
        return self._sale.id

    def get_person_name(self):
        if self._sale.client:
            return self._sale.client.person.name

    def confirm(self):
        paid = [p.is_paid() for p in self._sale.group.get_items()]
        if all(paid):
            self._sale.set_paid()


class _PurchaseConfirmationModel(_ConfirmationModel):
    def __init__(self, payments, group):
        purchase = PurchaseOrder.selectOneBy(group=group,
                                             connection=group.get_connection())
        if not isinstance(purchase, PurchaseOrder):
            raise TypeError("purchase must be a PurchaseOrder")
        _ConfirmationModel.__init__(self, payments)
        self._purchase = purchase
        self.open_date = purchase.open_date.date()

    def get_order_number(self):
        return self._purchase.id

    def get_person_name(self):
        if self._purchase.supplier:
            return self._purchase.supplier.person.name


class _LonelyConfirmationModel(_ConfirmationModel):
    def __init__(self, payments):
        self._payment = payments[0]
        _ConfirmationModel.__init__(self, payments)
        self.open_date = self._payment.open_date.date()

    def get_order_number(self):
        return -1

    def get_person_name(self):
        return u"None"

    def get_penalty(self):
        return self._payment.penalty

    def set_penalty(self, penalty):
        self._payment.penalty = penalty

    def get_interest(self):
        return self._payment.interest

    def set_interest(self, interest):
        self._payment.interest = interest

    def get_discount(self):
        return self._payment.discount

    def set_discount(self, discount):
        self._payment.discount = discount

    def get_total_value(self):
        return currency(self._payment.paid_value)


class _InstallmentConfirmationSlave(BaseEditor):
    """This slave is responsible for confirming a list of payments and
    applying the necessary interests and fines.

    """
    gladefile = 'InstallmentConfirmation'
    model_type = _ConfirmationModel
    size = (640, 420)
    title = _("Confirm payment")
    proxy_widgets = ('order_number',
                     'installment_value',
                     'interest',
                     'penalty',
                     'discount',
                     'total_value',
                     'person_name',
                     'pay_penalty',
                     'pay_interest',
                     'close_date')

    def __init__(self, conn, payments):
        """ Creates a new _InstallmentConfirmationSlave
        @param conn: a database connection
        @param payments: a list of payments
        """
        self._payments = payments
        self._proxy = None

        # We're about to pay a payment, fill in all paid_values
        # with the base value which is the initial value to be paid,
        # it'll be updated later on based on penalty, interest and discount
        # payment.paid_value will be updated *again* when we call
        # payment.pay with the calculated value
        for payment in self._payments:
            payment.paid_value = payment.value
        BaseEditor.__init__(self, conn)
        self._setup_widgets()

    def run_details_dialog(self):
        """ This can be overriden to provide a custom dialog when the
        user click in the details button.
        """

    # Private

    def _get_columns(self):
        return [Column('id', data_type=int, visible=False,
                       sorted=True),
                Column('description', _("Description"), data_type=str),
                Column('due_date', _("Due"), data_type=datetime.date),
                Column('paid_date', _("Paid date"), data_type=datetime.date),
                Column('base_value', _("Value"), data_type=currency),
                Column('paid_value', _("Paid value"), data_type=currency)]

    def _setup_widgets(self):
        self.installments.set_columns(self._get_columns())
        self.installments.extend(self._payments)
        self.installments_number = len(self._payments)
        self._update_interest(pay_interest=True)
        self._update_penalty(pay_penalty=True)
        self._update_total_value()
        self._update_accounts()

    def _update_interest(self, pay_interest):
        self.interest.set_sensitive(pay_interest)
        if pay_interest:
            interest = self.model.get_calculated_interest()
        else:
            interest = currency(0)

        self.model.set_interest(interest)
        self._proxy.update('interest')

    def _update_penalty(self, pay_penalty):
        self.penalty.set_sensitive(pay_penalty)
        if pay_penalty:
            penalty = self.model.get_calculated_penalty()
        else:
            penalty = currency(0)

        self.model.set_penalty(penalty)
        self._proxy.update('penalty')

    def _update_total_value(self):
        total = self.model.get_penalty() + self.model.get_interest() - \
                self.model.get_discount()
        value = total / self.installments_number
        for payment in self._payments:
            payment.paid_value = payment.value + value
            self.installments.update(payment)
        self._proxy.update('total_value')

    def _update_accounts(self):
        if len(self._payments) != 1:
            return
        register_payment_operations()

        payment = self._payments[0]
        create_transaction = payment.method.operation.create_transaction()
        self.account.set_sensitive(create_transaction)
        if not create_transaction:
            return

        destinations = Account.select(connection=self.conn)
        items = [(a.long_description, a) for a in destinations]
        self.account.prefill(sorted(items))
        self.account.select(payment.method.destination_account)

    #
    # BaseEditorSlave hooks
    #

    def setup_proxies(self):
        self._proxy = self.add_proxy(
            self.model, _InstallmentConfirmationSlave.proxy_widgets)

    def on_confirm(self):
        pay_date = self.close_date.get_date()
        for payment in self._payments:
            payment.pay(pay_date, payment.paid_value,
                        account=self.account.get_selected())
        self.model.confirm()
        return True

    #
    # Callbacks
    #

    def on_close_date__validate(self, widget, date):
        if sysparam(self.conn).ALLOW_OUTDATED_OPERATIONS:
            return

        if date > datetime.date.today() or date < self.model.open_date:
            return ValidationError(_("Paid date must be between "
                                     "%s and today") % (self.model.open_date, ))

    def after_penalty__content_changed(self, proxy_entry):
        if proxy_entry.is_valid() and proxy_entry.read() == ValueUnset:
            self.model.set_penalty(currency(0))
        self._update_total_value()

    def on_penalty__validate(self, entry, value):
        if value < 0:
            return ValidationError(_("Penalty can not be less than zero"))

    def after_interest__content_changed(self, proxy_entry):
        if proxy_entry.is_valid() and proxy_entry.read() == ValueUnset:
            self.model.set_interest(currency(0))
        self._update_total_value()

    def on_interest__validate(self, entry, value):
        if value < 0:
            return ValidationError(_("Interest can not be less than zero"))

    def after_discount__content_changed(self, proxy_entry):
        if proxy_entry.is_valid() and proxy_entry.read() == ValueUnset:
            self.model.set_discount(currency(0))
        self._update_total_value()

    def on_discount__validate(self, entry, value):
        total = self.model.get_installment_value()
        if value >= total:
            return ValidationError(_("Discount can not be greater or "
                                     "equal than %.2f" % (total, )))
        if value < 0:
            return ValidationError(_("Discount can not be less than zero"))

    def on_pay_penalty__toggled(self, toggle):
        self._update_penalty(pay_penalty=toggle.get_active())
        self._update_total_value()

    def on_pay_interest__toggled(self, toggle):
        self._update_interest(pay_interest=toggle.get_active())
        self._update_total_value()

    def on_details_button__clicked(self, widget):
        self.run_details_dialog()


class SaleInstallmentConfirmationSlave(_InstallmentConfirmationSlave):
    model_type = _ConfirmationModel

    def _lonely_setup_widgets(self):
        _InstallmentConfirmationSlave._setup_widgets(self)
        self.order_label.hide()
        self.person_label.hide()
        self.order_number.hide()
        self.person_name.hide()
        self.details_button.hide()

    def create_model(self, conn):
        group = self._payments[0].group
        if group and group.sale:
            return _SaleConfirmationModel(self._payments, group.sale)
        else:
            self._setup_widgets = self._lonely_setup_widgets
            return _LonelyConfirmationModel(self._payments)

    def run_details_dialog(self):
        sale_view = SaleView.select(
                        SaleView.q.id == self.model.get_order_number())[0]
        run_dialog(SaleDetailsDialog, self, self.conn, sale_view)

    def on_close_date__changed(self, proxy_date_entry):
        self._proxy.update('penalty')
        self._proxy.update('interest')
        self._proxy.update('total_value')


class PurchaseInstallmentConfirmationSlave(_InstallmentConfirmationSlave):
    model_type = _ConfirmationModel

    def _setup_widgets(self):
        _InstallmentConfirmationSlave._setup_widgets(self)
        self.discount_label.show()
        self.discount.show()
        self.person_label.set_text(_("Supplier: "))
        self.expander.hide()

        if isinstance(self.model, _LonelyConfirmationModel):
            self.order_label.hide()
            self.person_label.hide()
            self.order_number.hide()
            self.person_name.hide()
            self.details_button.hide()

    def create_model(self, conn):
        group = self._payments[0].group
        if group and group.purchase:
            model = _PurchaseConfirmationModel(self._payments, group)
        else:
            model = _LonelyConfirmationModel(self._payments)
        return model

    def run_details_dialog(self):
        purchase = self.model._purchase
        run_dialog(PurchaseDetailsDialog, self, self.conn, purchase)
