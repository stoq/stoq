# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007-2012 Async Open Source <http://www.async.com.br>
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
## Foundation, Outc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
##
""" Editor for payments descriptions and categories"""

import collections

from kiwi import ValueUnset
from kiwi.currency import currency
from kiwi.datatypes import ValidationError
from kiwi.ui.forms import BoolField, ChoiceField, DateField, PriceField, TextField

from stoqlib.api import api
from stoqlib.domain.account import Account
from stoqlib.domain.payment.category import PaymentCategory
from stoqlib.domain.payment.group import PaymentGroup
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.person import Client, Supplier, Branch
from stoqlib.domain.sale import SaleView
from stoqlib.exceptions import SellError
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.dialogs.stockdecreasedialog import StockDecreaseDetailsDialog
from stoqlib.gui.dialogs.paymentdetails import LonelyPaymentDetailsDialog
from stoqlib.gui.dialogs.purchasedetails import PurchaseDetailsDialog
from stoqlib.gui.dialogs.renegotiationdetails import RenegotiationDetailsDialog
from stoqlib.gui.dialogs.saledetails import SaleDetailsDialog
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.gui.fields import (AttachmentField, PaymentCategoryField,
                                PersonField, PaymentMethodField,
                                PersonQueryField)
from stoqlib.lib.dateutils import (get_interval_type_items,
                                   interval_type_as_relativedelta,
                                   localtoday)
from stoqlib.lib.decorators import cached_property
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext
_ONCE = -1


class _PaymentEditor(BaseEditor):
    confirm_widgets = ['due_date']
    model_type = Payment
    model_name = _('payment')

    # Override in subclass
    person_type = None
    category_type = None
    payment_type = None
    account_label = None

    @cached_property()
    def fields(self):
        return collections.OrderedDict(
            branch_id=PersonField(_('Branch'), proxy=True, person_type=Branch,
                                  can_add=False, can_edit=False, mandatory=True),
            method=PaymentMethodField(_('Method'),
                                      payment_type=self.payment_type,
                                      proxy=True, mandatory=True, separate=True),
            account=ChoiceField(self.account_label),
            description=TextField(_('Description'), proxy=True, mandatory=True),
            person=PersonQueryField(person_type=self.person_type, proxy=True),
            value=PriceField(_('Value'), proxy=True, mandatory=True),
            due_date=DateField(_('Due date'), proxy=True, mandatory=True),
            category=PaymentCategoryField(_('Category'),
                                          category_type=self.category_type,
                                          proxy=True),
            repeat=ChoiceField(_('Repeat')),
            end_date=DateField(_('End date')),
            attachment=AttachmentField(_('Attachment'))
        )

    def __init__(self, store, model=None, category=None):
        """ A base class for additional payments

        :param store: a store
        :param model: a :class:`stoqlib.domain.payment.payment.Payment` object or None

        """
        BaseEditor.__init__(self, store, model)
        self._setup_widgets()
        if category:
            self.category.select_item_by_label(category)
        self.description.grab_focus()

    #
    # BaseEditor hooks
    #

    def create_model(self, store):
        group = PaymentGroup()
        money = PaymentMethod.get_by_name(store, u'money')
        branch = api.get_current_branch(store)
        # Set status to PENDING now, to avoid calling set_pending on
        # on_confirm for payments that shoud not have its status changed.
        return Payment(open_date=localtoday().date(),
                       branch=branch,
                       status=Payment.STATUS_PENDING,
                       description=u'',
                       value=currency(0),
                       base_value=currency(0),
                       due_date=None,
                       method=money,
                       group=group,
                       category=None,
                       payment_type=self.payment_type,
                       bill_received=False)

    def setup_proxies(self):
        repeat_types = get_interval_type_items(with_multiples=True,
                                               adverb=True)
        repeat_types.insert(0, (_('Once'), _ONCE))
        self.repeat.prefill(repeat_types)
        is_paid = self.model.is_paid()
        # Show account information only after the payment is paid
        if is_paid:
            accounts = Account.get_accounts(self.store)
            self.account.prefill(api.for_combo(accounts, attr='long_description'))
            if self.payment_type == Payment.TYPE_OUT:
                account = self.model.transaction.source_account
            else:
                account = self.model.transaction.account
            self.account.select(account)
            self.account.set_property('sensitive', False)
        else:
            self.account.hide()
            self.account_lbl.hide()
        self.add_proxy(self.model, _PaymentEditor.proxy_widgets)

    def validate_confirm(self):
        if (self.repeat.get_selected() != _ONCE and
                not self._validate_date()):
            return False
        # FIXME: the kiwi view should export it's state and it should
        #        be used by default
        return bool(self.model.description and
                    self.model.due_date and
                    self.model.value)

    def on_confirm(self):
        self.model.base_value = self.model.value
        facet = self.person.read()
        if facet and facet is not ValueUnset:
            setattr(self.model.group,
                    self.person_attribute,
                    facet.person)

        self.model.attachment = self.fields['attachment'].attachment

        self.store.add(self.model.group)
        self.store.add(self.model)

        if self.repeat.get_selected() != _ONCE:
            Payment.create_repeated(self.store, self.model,
                                    self.repeat.get_selected(),
                                    self.model.due_date.date(),
                                    self.end_date.get_date())

    # Private

    def _setup_widgets(self):
        self.person_lbl.set_label(self._person_label)
        if self.model.group.sale:
            label = _("Sale details")
        elif self.model.group.purchase:
            label = _("Purchase details")
        elif self.model.group._renegotiation:
            label = _("Details")
        else:
            label = _("Details")
        self.details_button = self.add_button(label)
        self.details_button.connect('clicked',
                                    self._on_details_button__clicked)

        self.end_date.set_sensitive(False)
        if self.edit_mode:
            for field_name in ['value', 'due_date', 'person',
                               'repeat', 'end_date', 'branch_id', 'method']:
                field = self.fields[field_name]
                field.can_add = False
                field.can_edit = False
                field.set_sensitive(False)

        person = getattr(self.model.group, self.person_attribute)
        if person:
            store = person.store
            facet = store.find(self.person_type, person=person).one()
            self.fields['person'].set_value(facet)

    def _show_order_dialog(self):
        group = self.model.group
        if group.sale:
            sale_view = self.store.find(SaleView, id=group.sale.id).one()
            run_dialog(SaleDetailsDialog, self, self.store, sale_view)
        elif group.purchase:
            run_dialog(PurchaseDetailsDialog, self, self.store, group.purchase)
        elif group._renegotiation:
            run_dialog(RenegotiationDetailsDialog, self, self.store,
                       group._renegotiation)
        elif group.stock_decrease:
            run_dialog(StockDecreaseDetailsDialog, self, self.store,
                       group.stock_decrease)
        else:
            run_dialog(LonelyPaymentDetailsDialog, self, self.store, self.model)

    def _get_min_date_for_interval(self, due_date, interval_type):
        if not due_date or interval_type is None:
            return None
        return due_date + interval_type_as_relativedelta(interval_type)

    def _validate_date(self):
        if not self.end_date.props.sensitive:
            return True
        end_date = self.end_date.get_date()
        due_date = self.due_date.get_date()
        min_date = self._get_min_date_for_interval(due_date, self.repeat.read())

        if end_date and due_date:
            if end_date < due_date:
                self.end_date.set_invalid(_("End date cannot be before start date"))
            elif min_date and end_date < min_date:
                self.end_date.set_invalid(_("End date must be after %s for this "
                                            "repeat interval") %
                                          min_date.strftime('%x'))
            else:
                self.end_date.set_valid()
                self.refresh_ok(self.is_valid)
                return True
        elif not end_date:
            self.end_date.set_invalid(_("Date cannot be empty"))
        elif not due_date:
            self.due_date.set_invalid(_("Date cannot be empty"))
        self.refresh_ok(False)
        return False

    def _validate_person(self):
        payment_type = self.payment_type
        method = self.method.get_selected()
        self.person.set_property('mandatory',
                                 method.operation.require_person(payment_type))

    #
    # Kiwi Callbacks
    #

    def on_value__validate(self, widget, newvalue):
        if newvalue is None or newvalue <= 0:
            return ValidationError(_("The value must be greater than zero."))

    def on_repeat__content_changed(self, repeat):
        if repeat.get_selected() == _ONCE:
            self.end_date.set_sensitive(False)

            # FIXME: need this check so tests won't crash
            if hasattr(self, 'main_dialog'):
                self.refresh_ok(True)

            return

        self.end_date.set_sensitive(True)
        self._validate_date()

    def on_due_date__content_changed(self, due_date):
        self._validate_date()

    def on_end_date__content_changed(self, end_date):
        self._validate_date()

    def _on_details_button__clicked(self, widget):
        self._show_order_dialog()

    def on_method__content_changed(self, method):
        self.person.validate(force=True)
        self._validate_person()


class InPaymentEditor(_PaymentEditor):
    payment_type = Payment.TYPE_IN
    person_attribute = 'payer'
    person_type = Client
    _person_label = _("Payer:")
    account_label = _("Destination account")
    help_section = 'account-receivable'
    category_type = PaymentCategory.TYPE_RECEIVABLE

    def on_person__validate(self, widget, value):
        if not value:
            return

        try:
            # FIXME: model is not being updated correctly
            value.can_purchase(self.method.read(), self.value.read())
        except SellError as e:
            return ValidationError(e)

    def on_value__changed(self, value):
        self.person.validate(force=True)


class OutPaymentEditor(_PaymentEditor):
    payment_type = Payment.TYPE_OUT
    person_attribute = 'recipient'
    person_type = Supplier
    _person_label = _("Recipient:")
    account_label = _("Source account")
    help_section = 'account-payable'
    category_type = PaymentCategory.TYPE_PAYABLE

    @cached_property()
    def fields(self):
        fields = super(OutPaymentEditor, self).fields
        fields['bill_received'] = BoolField(_('The bill has arrived.'), proxy=True)
        return fields


def get_dialog_for_payment(payment):
    if payment is None:
        raise TypeError(payment)

    if payment.is_inpayment():
        return InPaymentEditor

    if payment.is_outpayment():
        return OutPaymentEditor

    raise TypeError(payment)


def test():  # pragma nocover
    creator = api.prepare_test()
    retval = run_dialog(InPaymentEditor, None, creator.store, None)
    creator.store.confirm(retval)


if __name__ == '__main__':  # pragma nocover
    test()
