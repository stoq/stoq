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
""" Payment confirm slave """

# FIXME: Move this module to stoqlib.gui.editors. There are no slaves here

import datetime
import os

import gio
import glib
from kiwi import ValueUnset
from kiwi.currency import currency
from kiwi.datatypes import ValidationError
from kiwi.ui.objectlist import Column

from stoqlib.api import api
from stoqlib.domain.account import Account
from stoqlib.domain.attachment import Attachment
from stoqlib.domain.costcenter import CostCenter
from stoqlib.domain.purchase import PurchaseOrder
from stoqlib.domain.sale import Sale, SaleView
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.dialogs.purchasedetails import PurchaseDetailsDialog
from stoqlib.gui.dialogs.saledetails import SaleDetailsDialog
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.gui.utils.filters import get_filters_for_attachment
from stoqlib.lib.dateutils import localtoday
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class _ConfirmationModel(object):
    def __init__(self, payments):
        self.payments = payments
        self.close_date = localtoday().date()

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

    def get_calculated_interest(self, pay_penalty):
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

    def get_calculated_interest(self, pay_penalty):
        return currency(sum(p.get_interest(self.close_date,
                                           pay_penalty=self.pay_penalty)
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

    def get_order_id(self):
        return self._sale.id

    def get_identifier(self):
        return self._sale.identifier

    def get_person_name(self):
        if self._sale.client:
            return self._sale.client.person.name


class _PurchaseConfirmationModel(_ConfirmationModel):
    def __init__(self, payments, group):
        purchase = group.store.find(PurchaseOrder, group=group).one()
        if not isinstance(purchase, PurchaseOrder):
            raise TypeError("purchase must be a PurchaseOrder")
        _ConfirmationModel.__init__(self, payments)
        self._purchase = purchase
        self.open_date = purchase.open_date.date()

    def get_order_id(self):
        return self._purchase.id

    def get_identifier(self):
        return self._purchase.identifier

    def get_person_name(self):
        if self._purchase.supplier:
            return self._purchase.supplier.person.name


class _LonelyConfirmationModel(_ConfirmationModel):
    def __init__(self, payments):
        self.pay_interest = True
        self.pay_penalty = True
        self._payment = payments[0]
        _ConfirmationModel.__init__(self, payments)
        self.open_date = self._payment.open_date.date()

    def get_order_id(self):
        return -1

    def get_identifier(self):
        return -1

    def get_person_name(self):
        return u"None"

    def get_calculated_penalty(self):
        return currency(sum(p.get_penalty(self.close_date)
                            for p in self.payments))

    def get_calculated_interest(self, pay_penalty):
        return currency(sum(p.get_interest(self.close_date,
                                           pay_penalty=self.pay_penalty)
                            for p in self.payments))

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


# FIXME: Not a slave: s/Slave/Editor/
class _PaymentConfirmSlave(BaseEditor):
    """This slave is responsible for confirming a list of payments and
    applying the necessary interests and fines.

    """
    gladefile = 'PaymentConfirmSlave'
    model_type = _ConfirmationModel
    size = (-1, 450)
    title = _("Confirm payment")
    proxy_widgets = ('identifier',
                     'installment_value',
                     'interest',
                     'penalty',
                     'discount',
                     'total_value',
                     'person_name',
                     'pay_penalty',
                     'pay_interest',
                     'close_date',
                     'cost_center')

    def __init__(self, store, payments, show_till_info=True):
        """ Creates a new _PaymentConfirmSlave

        :param store: a store
        :param payments: a list of payments
        :param show_till_info: if we should show an info message
            explaining that this operation wont generate a till entry.
        """
        self._show_till_info = show_till_info
        self._payments = payments
        self._proxy = None

        # We're about to pay a payment, fill in all paid_values
        # with the base value which is the initial value to be paid,
        # it'll be updated later on based on penalty, interest and discount
        # payment.paid_value will be updated *again* when we call
        # payment.pay with the calculated value
        for payment in self._payments:
            payment.paid_value = payment.value
        BaseEditor.__init__(self, store)
        self._setup_widgets()

    def run_details_dialog(self):
        """ This can be overriden to provide a custom dialog when the
        user click in the details button.
        """

    # Private

    def _get_columns(self):
        return [Column('identifier', _('Payment #'), data_type=int, width=60,
                       visible=False, format_func=str, sorted=True),
                Column('description', _("Description"), data_type=str),
                Column('due_date', _("Due"), data_type=datetime.date),
                Column('paid_date', _("Paid date"), data_type=datetime.date),
                Column('base_value', _("Value"), data_type=currency),
                Column('paid_value', _("Paid value"), data_type=currency)]

    def _setup_widgets(self):
        self.installments.set_columns(self._get_columns())
        self.installments.extend(self._payments)
        self.installments_number = len(self._payments)
        self._update_penalty(pay_penalty=self.pay_penalty.get_active())
        self._update_interest(pay_interest=self.pay_interest.get_active(),
                              pay_penalty=self.pay_penalty.get_active())
        self._update_total_value()
        self._update_accounts()
        self.cost_center_lbl.hide()
        self.cost_center.hide()

        # Attachments are added to single payments, therefore it's only allowed
        # if you are paying a single payment. If you want to add attachments
        # even then, edit them individually in the Payable main window later.
        if len(self._payments) > 1:
            self.attachment_lbl.hide()
            self.attachment_chooser.hide()
        else:
            self._attachment = self._payments[0].attachment
            self._setup_attachment_chooser()

        if isinstance(self.model, _LonelyConfirmationModel):
            self.identifier_lbl.hide()
            self.person_label.hide()
            self.identifier.hide()
            self.person_name.hide()
            self.details_button.hide()

        if (self._show_till_info and
                any([p.method.method_name == u'money' for
                     p in self._payments])):
            self.set_message(self.get_till_info_msg())

    def _update_interest(self, pay_interest, pay_penalty):
        self.interest.set_sensitive(pay_interest)
        if pay_interest:
            interest = self.model.get_calculated_interest(pay_penalty=pay_penalty)
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

        payment = self._payments[0]
        create_transaction = payment.method.operation.create_transaction()
        for combo in [self.destination_account, self.source_account]:
            combo.set_sensitive(create_transaction)

        if not create_transaction:
            return

        destination_combo = self.get_account_destination_combo()
        for combo in [self.destination_account, self.source_account]:
            combo.prefill(api.for_combo(
                self.store.find(Account),
                attr='long_description'))

            if combo is destination_combo:
                combo.select(payment.method.destination_account)
            else:
                combo.select(
                    sysparam.get_object(self.store, 'IMBALANCE_ACCOUNT'))

    def _setup_attachment_chooser(self):
        self.attachment_chooser.connect('file-set',
                                        self._on_attachment_chooser__file_set)

        # If payment already had an attachment attached, changes the
        # FileChooser label to that file's name.
        if self._attachment and self._attachment.blob:
            name = self._attachment.get_description()
            # We can't use self.attachment_chooser.set_filename() because the
            # attachment is not a real file in the filesystem, but a field in
            # the database.
            label = (self.attachment_chooser.
                     get_children()[0].get_children()[0].get_children()[1])
            # We need to use glib.idle_add() so the label.set_label() will be
            # run once gtk main loop is done drawing the button (so it won't
            # overwrite to label back to '(None)').
            glib.idle_add(label.set_label, name)

        for ffilter in get_filters_for_attachment():
            self.attachment_chooser.add_filter(ffilter)

    def _on_attachment_chooser__file_set(self, button):
        filename = self.attachment_chooser.get_filename()
        data = open(filename, 'rb').read()
        mimetype = unicode(gio.content_type_guess(filename, data, False))

        if self._attachment is None:
            self._attachment = Attachment(store=self.store)
        self._attachment.name = unicode(os.path.basename(filename))
        self._attachment.mimetype = mimetype
        self._attachment.blob = data

    #
    # BaseEditorSlave hooks
    #

    def setup_proxies(self):
        self._proxy = self.add_proxy(
            self.model, _PaymentConfirmSlave.proxy_widgets)

    def on_confirm(self):
        cost_center = self.cost_center.read()
        if cost_center not in (ValueUnset, None):
            cost_center.add_lonely_payment(self.model._payment)
        if len(self._payments) == 1:
            self._payments[0].attachment = self._attachment
        pay_date = self.close_date.get_date()
        for payment in self._payments:
            transaction_number = self.account_transaction_number.read()
            if not transaction_number or transaction_number is ValueUnset:
                transaction_number = None

            payment.pay(pay_date, payment.paid_value,
                        source_account=self.source_account.get_selected(),
                        destination_account=self.destination_account.get_selected(),
                        account_transaction_number=transaction_number)
        self.model.confirm()

    def get_till_info_msg(self):
        raise NotImplementedError

    def get_account_destination_combo(self):
        raise NotImplementedError

    #
    # Callbacks
    #

    def on_close_date__validate(self, widget, date):
        if sysparam.get_bool('ALLOW_OUTDATED_OPERATIONS'):
            return

        if date > localtoday().date() or date < self.model.open_date:
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
                                     "equal than %.2f") % (total, ))
        if value < 0:
            return ValidationError(_("Discount can not be less than zero"))

    def on_pay_penalty__toggled(self, toggle):
        self._update_penalty(pay_penalty=toggle.get_active())
        self._update_interest(pay_interest=self.pay_interest.get_active(),
                              pay_penalty=toggle.get_active())
        self._update_total_value()

    def on_pay_interest__toggled(self, toggle):
        self._update_interest(pay_interest=toggle.get_active(),
                              pay_penalty=self.pay_penalty.get_active())
        self._update_total_value()

    def on_details_button__clicked(self, widget):
        self.run_details_dialog()


# FIXME: Not a slave: s/Slave/Editor/
class SalePaymentConfirmSlave(_PaymentConfirmSlave):
    model_type = _ConfirmationModel
    help_section = "account-receivable-receive"

    def _setup_widgets(self):
        _PaymentConfirmSlave._setup_widgets(self)

    def get_till_info_msg(self):
        # TRANSLATORS: 'cash addition' is 'suprimento' in pt_BR
        return _("Note that this operation will not generate a till entry for "
                 "the money payment(s). \nIf you are adding money on the "
                 "till, do a cash addition in the Till applications too.")

    def get_account_destination_combo(self):
        return self.destination_account

    def create_model(self, store):
        group = self._payments[0].group
        if group and group.sale:
            return _SaleConfirmationModel(self._payments, group.sale)
        else:
            return _LonelyConfirmationModel(self._payments)

    def run_details_dialog(self):
        sale_id = self.model.get_order_id()
        sale_view = self.store.find(SaleView, id=sale_id).one()
        run_dialog(SaleDetailsDialog, self, self.store, sale_view)

    def on_close_date__changed(self, proxy_date_entry):
        self._proxy.update('penalty')
        self._proxy.update('interest')
        self._proxy.update('total_value')


# FIXME: Not a slave: s/Slave/Editor/
class PurchasePaymentConfirmSlave(_PaymentConfirmSlave):
    model_type = _ConfirmationModel
    help_section = "account-payable-pay"

    def _setup_widgets(self):
        _PaymentConfirmSlave._setup_widgets(self)
        self.discount_label.show()
        self.discount.show()
        self.person_label.set_text(_("Supplier: "))
        self.expander.hide()
        self.pay_penalty.set_active(True)
        self.pay_interest.set_active(True)
        self._fill_cost_center_combo()

    def get_till_info_msg(self):
        # TRANSLATORS: 'cash removal' is 'sangria' in pt_BR
        return _("Note that this operation will not generate a till entry for "
                 "the money payment(s). \nIf you are removing money from the "
                 "till, do a cash removal in the Till application too.")

    def get_account_destination_combo(self):
        return self.source_account

    def create_model(self, store):
        group = self._payments[0].group
        if group and group.purchase:
            model = _PurchaseConfirmationModel(self._payments, group)
        else:
            model = _LonelyConfirmationModel(self._payments)
        return model

    def run_details_dialog(self):
        purchase = self.model._purchase
        run_dialog(PurchaseDetailsDialog, self, self.store, purchase)

    def _fill_cost_center_combo(self):
        cost_centers = CostCenter.get_active(self.store)

        # we keep this value because each call to is_empty() is a new sql query
        # to the database
        cost_centers_exists = not cost_centers.is_empty()

        if (cost_centers_exists and isinstance(self.model,
                                               _LonelyConfirmationModel)):
            self.cost_center.prefill(api.for_combo(cost_centers, attr='name',
                                                   empty=_('No cost center.')))
            self.cost_center.set_visible(cost_centers_exists)
            self.cost_center_lbl.set_visible(cost_centers_exists)
