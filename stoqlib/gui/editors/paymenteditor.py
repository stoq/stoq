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

from dateutil.relativedelta import relativedelta
import gtk
import pango
from kiwi.datatypes import currency, ValidationError, ValueUnset
from kiwi.ui.widgets.list import Column

from stoqlib.api import api
from stoqlib.domain.interfaces import (IInPayment, IOutPayment, IClient,
                                       ISupplier)
from stoqlib.domain.payment.category import PaymentCategory
from stoqlib.domain.payment.group import PaymentGroup
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.payment.views import PaymentChangeHistoryView
from stoqlib.domain.person import PersonAdaptToClient, PersonAdaptToSupplier
from stoqlib.domain.sale import SaleView
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.dialogs.purchasedetails import PurchaseDetailsDialog
from stoqlib.gui.dialogs.renegotiationdetails import RenegotiationDetailsDialog
from stoqlib.gui.dialogs.saledetails import SaleDetailsDialog
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.gui.editors.paymentcategoryeditor import PaymentCategoryEditor
from stoqlib.gui.editors.personeditor import ClientEditor, SupplierEditor
from stoqlib.gui.wizards.personwizard import run_person_role_dialog
from stoqlib.lib.defaults import (INTERVALTYPE_WEEK,
                                  INTERVALTYPE_MONTH)
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext
INTERVALTYPE_ONCE = -1
INTERVALTYPE_BIWEEKLY = 10
INTERVALTYPE_QUARTERLY = 11


class PaymentEditor(BaseEditor):
    gladefile = "PaymentEditor"
    model_type = Payment
    person_editor = None
    person_class = None
    person_iface = None
    title = _("Payment")
    confirm_widgets = ['due_date']
    proxy_widgets = ['value',
                     'description',
                     'due_date',
                     ]

    def __init__(self, conn, model=None):
        """ A base class for additional payments

        @param conn: a database connection
        @param model: a L{stoqlib.domain.payment.payment.Payment} object or None

        """
        BaseEditor.__init__(self, conn, model)
        self._setup_widgets()

    #
    # BaseEditor hooks
    #

    def create_model(self, trans):
        group = PaymentGroup(connection=trans)
        money = PaymentMethod.get_by_name(trans, 'money')
        # Set status to PENDING now, to avoid calling set_pending on
        # on_confirm for payments that shoud not have its status changed.
        return Payment(open_date=datetime.date.today(),
                       status=Payment.STATUS_PENDING,
                       description='',
                       value=currency(0),
                       base_value=currency(0),
                       due_date=None,
                       method=money,
                       group=group,
                       till=None,
                       category=None,
                       connection=trans)

    def setup_proxies(self):
        self._fill_category_combo()
        self._fill_method_combo()
        self._populate_person()
        self.repeat.prefill([
            (_('Once'), INTERVALTYPE_ONCE),
            (_('Weekly'), INTERVALTYPE_WEEK),
            (_('Biweekly'), INTERVALTYPE_BIWEEKLY),
            (_('Monthly'), INTERVALTYPE_MONTH),
            (_('Quarterly'), INTERVALTYPE_QUARTERLY)])
        self.add_category.set_tooltip_text(_("Add a new payment category"))
        self.edit_category.set_tooltip_text(_("Edit the selected payment category"))
        if self.person_iface == ISupplier:
            self.add_person.set_tooltip_text(_("Add a new supplier"))
            self.edit_person.set_tooltip_text(_("Edit the selected supplier"))
        else:
            self.add_person.set_tooltip_text(_("Add a new client"))
            self.edit_person.set_tooltip_text(_("Edit the selected client"))
        self.add_proxy(self.model, PaymentEditor.proxy_widgets)

    def validate_confirm(self):
        if (self.repeat.get_selected() != INTERVALTYPE_ONCE and
            not self._validate_date()):
            return False
        # FIXME: the kiwi view should export it's state and it should
        #        be used by default
        return bool(self.model.description and
                    self.model.due_date and
                    self.model.value)

    def on_confirm(self):
        self.model.base_value = self.model.value
        person = self.person.get_selected_data()
        if person is not None and person is not ValueUnset:
            setattr(self.model.group,
                    self.person_attribute,
                    person.person)
        self.model.category = self.category.get_selected()
        method = self.method.get_selected()
        if method is not None:
            self.model.method = method

        if self.repeat.get_selected() != INTERVALTYPE_ONCE:
            self._create_repeated_payments()
        return self.model

    def can_edit_details(self):
        for widget in [self.value, self.due_date,
                       self.add_person, self.repeat, self.method]:
            widget.set_sensitive(True)
        self.details_button.hide()
        self.edit_person.set_sensitive(bool(self.person.get_selected()))
        self._populate_person()

    # Private

    def _populate_person(self):
        if self.person_class == PersonAdaptToSupplier:
            facets = self.person_class.get_active_suppliers(self.trans)
        else:
            facets = self.person_class.get_active_clients(self.trans)

        if facets:
            self.person.prefill(sorted([(f.person.name, f)
                                        for f in facets]))
        self.person.set_sensitive(bool(facets))

        person = getattr(self.model.group, self.person_attribute)
        if person:
            facet = self.person_iface(person)
            self.person.select(facet)

    def _run_payment_category_editor(self, category=None):
        trans = api.new_transaction()
        category = trans.get(category)
        model = run_dialog(PaymentCategoryEditor, self, trans, category)
        rv = api.finish_transaction(trans, model)
        trans.close()
        if rv:
            self._fill_category_combo()
            self.category.select(model)

    def _run_person_editor(self, person=None):
        trans = api.new_transaction()
        person = trans.get(person)
        model = run_person_role_dialog(self.person_editor, self, trans, person)
        rv = api.finish_transaction(trans, model)
        trans.close()
        if rv:
            self._populate_person()
            self.person.select(model)

    def _fill_category_combo(self):
        categories = PaymentCategory.select(
            connection=self.trans).orderBy('name')
        self.category.set_sensitive(bool(categories))
        categories = [(c.name, c) for c in categories]
        categories.insert(0, (_('No category'), None))
        self.category.prefill(categories)
        self.category.select(self.model.category)
        self.edit_category.set_sensitive(False)

    def _fill_method_combo(self):
        methods = PaymentMethod.select(
            connection=self.trans).orderBy('description')
        self.method.set_sensitive(False)
        self.method.prefill([(m.description, m) for m in methods
                             if m.is_active and m.method_name != 'multiple'])
        self.method.select(self.model.method)

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
        for widget in [self.value, self.due_date, self.person,
                       self.add_person, self.edit_person,
                       self.repeat, self.end_date]:
            widget.set_sensitive(False)

    def _show_order_dialog(self):
        group = self.model.group
        if group.sale:
            sale_view = SaleView.select(SaleView.q.id == group.sale.id)[0]
            run_dialog(SaleDetailsDialog, self, self.conn, sale_view)
        elif group.purchase:
            run_dialog(PurchaseDetailsDialog, self, self.conn, group.purchase)
        elif group._renegotiation:
            run_dialog(RenegotiationDetailsDialog, self, self.conn,
                       group._renegotiation)
        else:
            run_dialog(LonelyPaymentDetailsDialog, self, self.conn, self.model)

    def _validate_date(self):
        if not self.end_date.props.sensitive:
            return True
        end_date = self.end_date.get_date()
        due_date = self.due_date.get_date()
        if end_date and due_date:
            if end_date < due_date:
                self.end_date.set_invalid(_("End date must be before start date"))
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

    def _create_repeated_payments(self):
        start_date = self.model.due_date.date()
        end_date = self.end_date.get_date()
        repeat_type = self.repeat.get_selected()
        if repeat_type == INTERVALTYPE_WEEK:
            delta = relativedelta(weeks=1)
        elif repeat_type == INTERVALTYPE_BIWEEKLY:
            delta = relativedelta(weeks=2)
        elif repeat_type == INTERVALTYPE_MONTH:
            # Check if we're on the last day of month and make
            # sure the payment will always be the last day of the
            # month.
            next_date = start_date + relativedelta(days=1)
            if start_date.month != next_date.month:
                # This really means: last day of month, it'll never
                # cross month boundaries even if there are less than
                # 31 days.
                delta = relativedelta(months=1, day=31)
            else:
                delta = relativedelta(months=1, day=start_date.day)
        elif repeat_type == INTERVALTYPE_QUARTERLY:
            delta = relativedelta(months=3)
        else:
            raise AssertionError(repeat_type)

        next_date = start_date + delta
        dates = []
        while next_date < end_date:
            dates.append(next_date)
            next_date = next_date + delta
        if not dates:
            return
        description = self.model.description
        self.model.description = '1/%d %s' % (len(dates), description)
        for i, date in enumerate(dates):
            p = Payment(open_date=self.model.open_date,
                        status=self.model.status,
                        description='%d/%d %s' % (i + 1, len(dates),
                                                  description),
                        value=self.model.value,
                        base_value=self.model.base_value,
                        due_date=date,
                        method=self.model.method,
                        group=self.model.group,
                        till=self.model.till,
                        category=self.model.category,
                        connection=self.conn)
            if self.model.is_inpayment():
                p.addFacet(IInPayment, connection=self.conn)
            elif self.model.is_outpayment():
                p.addFacet(IOutPayment, connection=self.conn)

    #
    # Kiwi Callbacks
    #

    def on_value__validate(self, widget, newvalue):
        if newvalue is None or newvalue <= 0:
            return ValidationError(_("The value must be greater than zero."))

    def on_repeat__content_changed(self, repeat):
        self.end_date.set_sensitive(repeat.get_selected() != INTERVALTYPE_ONCE)
        self._validate_date()

    def on_due_date__content_changed(self, due_date):
        self._validate_date()

    def on_end_date__content_changed(self, end_date):
        self._validate_date()

    def on_category__content_changed(self, category):
        self.edit_category.set_sensitive(bool(self.category.get_selected()))

    def on_person__content_changed(self, person):
        self.edit_person.set_sensitive(bool(self.person.get_selected()))

    def on_add_category__clicked(self, widget):
        self._run_payment_category_editor()

    def on_edit_category__clicked(self, widget):
        self._run_payment_category_editor(self.category.get_selected())

    def on_add_person__clicked(self, widget):
        self._run_person_editor()

    def on_edit_person__clicked(self, widget):
        self._run_person_editor(self.person.get_selected())

    def _on_details_button__clicked(self, widget):
        self._show_order_dialog()


class InPaymentEditor(PaymentEditor):
    person_attribute = 'payer'
    person_editor = ClientEditor
    person_class = PersonAdaptToClient
    person_iface = IClient
    _person_label = _("Payer:")
    help_section = 'account-receivable'

    def __init__(self, conn, model=None):
        """ This dialog is responsible to create additional payments with
        IInPayment facet.

        @param conn: a database connection
        @param model: a L{stoqlib.domain.payment.payment.Payment} object
                      or None
        """
        PaymentEditor.__init__(self, conn, model)
        if model is None or not model.is_inpayment():
            self.model.addFacet(IInPayment, connection=self.conn)
            self.can_edit_details()


class OutPaymentEditor(PaymentEditor):
    person_attribute = 'recipient'
    person_editor = SupplierEditor
    person_class = PersonAdaptToSupplier
    person_iface = ISupplier
    _person_label = _("Recipient:")
    help_section = 'account-payable'

    def __init__(self, conn, model=None):
        """ This dialog is responsible to create additional payments with
        IOutPayment facet.

        @param conn: a database connection
        @param model: a L{stoqlib.domain.payment.payment.Payment} object
                      or None
        """
        PaymentEditor.__init__(self, conn, model)
        if model is None or not model.is_outpayment():
            self.model.addFacet(IOutPayment, connection=self.conn)
            self.can_edit_details()


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
                     'status']

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
        return [Column('change_date', _("When"),
                        data_type=datetime.date, sorted=True, ),
                Column('description', _("Payment"),
                        data_type=str, expand=True,
                        ellipsize=pango.ELLIPSIZE_END),
                Column('changed_field', _("Changed"),
                        data_type=str, justify=gtk.JUSTIFY_RIGHT),
                Column('from_value', _("From"),
                    data_type=str, justify=gtk.JUSTIFY_RIGHT),
                Column('to_value', _("To"),
                        data_type=str, justify=gtk.JUSTIFY_RIGHT),
                Column('reason', _("Reason"),
                        data_type=str, expand=True,
                        ellipsize=pango.ELLIPSIZE_END)]

    #
    # BaseEditor
    #

    def setup_proxies(self):
        self._proxy = self.add_proxy(
            self.model, LonelyPaymentDetailsDialog.proxy_widgets)

    def get_title(self, model):
        if model is None:
            return

        if model.is_inpayment():
            return _('Receiving Details')

        if model.is_outpayment():
            return _('Payment Details')


def get_dialog_for_payment(payment):
    if payment is None:
        raise TypeError(payment)

    if payment.is_inpayment():
        return InPaymentEditor

    if payment.is_outpayment():
        return OutPaymentEditor

    raise TypeError(payment)
