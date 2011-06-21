# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007-2011 Async Open Source <http://www.async.com.br>
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


import datetime

import gtk
import pango

from kiwi.datatypes import currency, ValidationError
from kiwi.ui.widgets.list import Column

from stoqlib.database.runtime import new_transaction, finish_transaction
from stoqlib.domain.interfaces import (IInPayment, IOutPayment, IClient,
                                       ISupplier)
from stoqlib.domain.payment.category import PaymentCategory
from stoqlib.domain.payment.group import PaymentGroup
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.payment.views import (InPaymentView, OutPaymentView,
                                          PaymentChangeHistoryView)
from stoqlib.domain.person import PersonAdaptToClient, PersonAdaptToSupplier
from stoqlib.domain.sale import SaleView
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.dialogs.purchasedetails import PurchaseDetailsDialog
from stoqlib.gui.dialogs.renegotiationdetails import RenegotiationDetailsDialog
from stoqlib.gui.dialogs.saledetails import SaleDetailsDialog
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.gui.editors.paymentcategoryeditor import PaymentCategoryEditor
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class BasePaymentEditor(BaseEditor):
    gladefile = "BasePaymentEditor"
    model_type = Payment
    title = _(u"Payment")
    proxy_widgets = ['value',
                     'description',
                     'due_date',
                     'category']

    def __init__(self, conn, model=None):
        """ A base class for additional payments

        @param conn: a database connection
        @param model: a L{stoqlib.domain.payment.payment.Payment} object or None

        """
        BaseEditor.__init__(self, conn, model)
        self.setup_widgets()

    #
    # BaseEditor hooks
    #

    def create_model(self, trans):
        group = PaymentGroup(connection=trans)
        money = PaymentMethod.get_by_name(trans, 'money')
        return Payment(open_date=datetime.date.today(),
                       description='',
                       value=currency(0),
                       base_value=currency(0),
                       due_date=None,
                       method=money,
                       group=group,
                       till=None,
                       category=None,
                       connection=trans)

    def on_due_date__activate(self, date):
        self.confirm()

    def setup_proxies(self):
        self._fill_category_combo()
        self.populate_person()
        self.add_proxy(self.model, BasePaymentEditor.proxy_widgets)

    def _fill_category_combo(self):
        categories = PaymentCategory.select(
            connection=self.trans).orderBy('name')
        self.category.set_sensitive(bool(categories))
        self.category.prefill([(c.name, c) for c in categories])

    def setup_widgets(self):
        self.person_label.set_label(self._person_label)
        self.details_button = self.add_button(self.details_button_label)
        self.details_button.connect('clicked',
                                    self._on_details_button__clicked)
        for widget in [self.value, self.due_date, self.person]:
            widget.set_sensitive(False)

    def validate_confirm(self):
        # FIXME: the kiwi view should export it's state and it shoul
        #        be used by default
        return bool(self.model.description and self.model.due_date and
                    self.model.value)

    def on_confirm(self):
        # Only set pending if its a new payment (status == PREVIEW)
        if self.model.status is Payment.STATUS_PREVIEW:
            self.model.set_pending()
        self.model.base_value = self.model.value
        person = self.person.get_selected_data()
        if person is not None:
            setattr(self.model.group,
                    self.person_attribute,
                    person.person)
        return self.model

    def can_edit_details(self):
        for widget in [self.value, self.due_date, self.person]:
            widget.set_sensitive(True)
        self.details_button.hide()

    #
    # Kiwi Callbacks
    #

    def on_value__validate(self, widget, newvalue):
        if newvalue is None or newvalue <= 0:
            return ValidationError(_(u"The value must be greater than zero."))

    def on_create_category__clicked(self, widget):
        trans = new_transaction()
        model = run_dialog(PaymentCategoryEditor, self, trans)
        rv = finish_transaction(trans, model)
        trans.close()
        if rv:
            self._fill_category_combo()
            self.category.update(model)


class InPaymentEditor(BasePaymentEditor):
    person_attribute = 'payer'
    details_button_label = _("Sale details")
    _person_label = _("Payer:")
    def __init__(self, conn, model=None):
        """ This dialog is responsible to create additional payments with
        IInPayment facet.

        @param conn: a database connection
        @param model: a L{stoqlib.domain.payment.payment.Payment} object
                      or None
        """
        BasePaymentEditor.__init__(self, conn, model)
        if not IInPayment(model, None):
            self.model.addFacet(IInPayment, connection=self.conn)
            self.can_edit_details()

    def populate_person(self):
        clients = PersonAdaptToClient.get_active_clients(self.trans)
        if clients:
            self.person.prefill(sorted([(c.person.name, c)
                                        for c in clients]))
        else:
            self.person.set_sensitive(False)

        payer = self.model.group.payer
        if payer:
            client = IClient(payer)
            self.person.select(client)

    def show_receivable_details(self, receivable_view):
        if receivable_view.sale_id is not None:
            sale_view = SaleView.select(
                    SaleView.q.id == receivable_view.sale_id)[0]
            run_dialog(SaleDetailsDialog, self, self.conn, sale_view)
        elif receivable_view.renegotiation_id is not None:
            run_dialog(RenegotiationDetailsDialog, self, self.conn,
                       receivable_view.renegotiation)
        else:
            payment = receivable_view.payment
            run_dialog(LonelyPaymentDetailsDialog, self, self.conn, payment)

    def _on_details_button__clicked(self, widget):
        payment = self.model
        receivable_view = InPaymentView.select(
                            InPaymentView.q.id == payment.id)[0]
        self.show_receivable_details(receivable_view)


class OutPaymentEditor(BasePaymentEditor):
    person_attribute = 'recipient'
    details_button_label = _(u"Order details")
    _person_label = _("Recipient:")
    def __init__(self, conn, model=None):
        """ This dialog is responsible to create additional payments with
        IOutPayment facet.

        @param conn: a database connection
        @param model: a L{stoqlib.domain.payment.payment.Payment} object
                      or None
        """
        BasePaymentEditor.__init__(self, conn, model)
        if not IOutPayment(model, None):
            self.model.addFacet(IOutPayment, connection=self.conn)
            self.can_edit_details()

    def populate_person(self):
        suppliers = PersonAdaptToSupplier.get_active_suppliers(self.trans)
        if suppliers:
            self.person.prefill(sorted([(s.person.name, s)
                                        for s in suppliers]))
        else:
            self.person.set_sensitive(False)

        supplier = self.model.group.recipient
        if supplier:
            supplier  = ISupplier(supplier)
            self.person.select(supplier)

    def show_payable_details(self, payable_view):
        if payable_view.purchase:
            run_dialog(PurchaseDetailsDialog, self,
                       self.conn, payable_view.purchase)
        elif payable_view.sale:
            run_dialog(SaleDetailsDialog, self,
                       self.conn, payable_view.sale)
        else:
            payment = payable_view.payment
            run_dialog(LonelyPaymentDetailsDialog, self, self.conn, payment)

    def _on_details_button__clicked(self, widget):
        payment = self.model
        payable_view = OutPaymentView.select(
                            OutPaymentView.q.id == payment.id)[0]
        self.show_payable_details(payable_view)


class LonelyPaymentDetailsDialog(BaseEditor):
    gladefile = 'LonelyPaymentDetailsDialog'
    model_type = Payment
    size = (550, 350)
    proxy_widgets = ['value',
                     'interest',
                     'paid_value',
                     'penalty',
                     'description',
                     'discount',
                     'due_date',
                     'paid_date',
                     'status',]

    def __init__(self, conn, payment):
        BaseEditor.__init__(self, conn, payment)
        self._setup_widgets()

    def _setup_widgets(self):
        self.payment_info_list.set_columns(self._get_columns())
        changes = PaymentChangeHistoryView.select_by_group(self.model.group,
                                                           connection=self.conn)
        self.payment_info_list.add_list(changes)

        # workaround to improve the dialog looking
        if self.model.paid_value:
            penalty = self._get_penalty()
            self.penalty.update(penalty)
            self.interest.update(self.model.interest)
        else:
            self.paid_value.update(currency(0))

    def _get_penalty(self):
        penalty = (self.model.paid_value -
          (self.model.value - self.model.discount + self.model.interest))

        return currency(penalty)

    def _get_columns(self):
        return [Column('change_date', _(u"When"),
                        data_type=datetime.date, sorted=True,),
                Column('description', _(u"Payment"),
                        data_type=str, expand=True,
                        ellipsize=pango.ELLIPSIZE_END),
                Column('changed_field', _(u"Changed"),
                        data_type=str, justify=gtk.JUSTIFY_RIGHT),
                Column('from_value', _(u"From"),
                    data_type=str, justify=gtk.JUSTIFY_RIGHT),
                Column('to_value', _(u"To"),
                        data_type=str, justify=gtk.JUSTIFY_RIGHT),
                Column('reason', _(u"Reason"),
                        data_type=str, expand=True,
                        ellipsize=pango.ELLIPSIZE_END)]

    #
    # BaseEditor
    #

    def setup_proxies(self):
        self._proxy = self.add_proxy(
            self.model, LonelyPaymentDetailsDialog.proxy_widgets)

    def get_title(self, model):
        if IInPayment(model, None):
            return _(u'Receiving Details')

        if IOutPayment(model, None):
            return _(u'Payment Details')

def get_dialog_for_payment(payment):
    if IInPayment(payment, None):
        return InPaymentEditor

    if IOutPayment(payment, None):
        return OutPaymentEditor

    raise TypeError(payment)
