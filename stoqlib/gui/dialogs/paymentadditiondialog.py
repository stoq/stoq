# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007 Async Open Source <http://www.async.com.br>
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
## Author(s):   Johan Dahlin          <jdahlin@async.com.br>
##
##
""" Dialog for adding simple payments """


import datetime

import pango
import gtk

from kiwi.datatypes import currency, ValidationError
from kiwi.ui.widgets.list import Column

from stoqlib.domain.interfaces import IInPayment, IOutPayment
from stoqlib.domain.payment.category import PaymentCategory
from stoqlib.domain.payment.group import PaymentGroup
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.payment.payment import Payment
from stoqlib.domain.payment.views import PaymentChangeHistoryView
from stoqlib.domain.person import PersonAdaptToClient, PersonAdaptToSupplier
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class BasePaymentAddition(BaseEditor):
    gladefile = "BasePaymentAddition"
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
                       destination=None,
                       connection=trans)

    def on_due_date__activate(self, date):
        self.confirm()

    def setup_proxies(self):
        categories = PaymentCategory.select(
            connection=self.trans).orderBy('name')
        if categories:
            self.category.prefill([(c.name, c) for c in categories])
        else:
            self.category.set_sensitive(False)

        self.populate_person()
        self.add_proxy(self.model, BasePaymentAddition.proxy_widgets)

    def validate_confirm(self):
        # FIXME: the kiwi view should export it's state and it shoul
        #        be used by default
        return bool(self.model.description and self.model.due_date and
                    self.model.value)

    def on_confirm(self):
        self.model.set_pending()
        self.model.base_value = self.model.value
        person = self.person.get_selected()
        if person is not None:
            setattr(self.model.group,
                    self.person_attribute,
                    person.person)
        return self.model

    #
    # Kiwi Callbacks
    #

    def on_value__validate(self, widget, newvalue):
        if newvalue is None or newvalue <= 0:
            return ValidationError(_(u"The value must be greater than zero."))


class InPaymentAdditionDialog(BasePaymentAddition):
    person_attribute = 'payer'
    def __init__(self, conn, model=None):
        """ This dialog is responsible to create additional payments with
        IInPayment facet.

        @param conn: a database connection
        @param model: a L{stoqlib.domain.payment.payment.Payment} object
                      or None
        """
        BasePaymentAddition.__init__(self, conn, model)
        self.model.addFacet(IInPayment, connection=self.conn)
        self.person_label.set_label(_("Payer:"))

    def populate_person(self):
        clients = PersonAdaptToClient.get_active_clients(self.trans)
        if clients:
            self.person.prefill(sorted([(c.person.name, c)
                                        for c in clients]))
        else:
            self.person.set_sensitive(False)


class OutPaymentAdditionDialog(BasePaymentAddition):
    person_attribute = 'recipient'
    def __init__(self, conn, model=None):
        """ This dialog is responsible to create additional payments with
        IOutPayment facet.

        @param conn: a database connection
        @param model: a L{stoqlib.domain.payment.payment.Payment} object
                      or None
        """
        BasePaymentAddition.__init__(self, conn, model)
        self.model.addFacet(IOutPayment, connection=self.conn)
        self.person_label.set_label(_("Recipient:"))

    def populate_person(self):
        suppliers = PersonAdaptToSupplier.get_active_suppliers(self.trans)
        if suppliers:
            self.person.prefill(sorted([(s.person.name, s)
                                        for s in suppliers]))
        else:
            self.person.set_sensitive(False)


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
