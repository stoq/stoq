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

from kiwi.datatypes import currency

from stoqlib.domain.interfaces import IInPayment, IOutPayment
from stoqlib.domain.payment.payment import Payment
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class BasePaymentAddition(BaseEditor):
    gladefile = "BasePaymentAddition"
    model_type = Payment
    title = _(u"Payment")
    proxy_widgets = ['value',
                     'description',
                     'due_date']

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
        return Payment(open_date=datetime.date.today(),
                          description='',
                          value=currency(0),
                          base_value=currency(0),
                          due_date=None,
                          method=None,
                          group=None,
                          till=None,
                          destination=None,
                          connection=trans)

    def on_due_date__activate(self, date):
        self.confirm()

    def setup_proxies(self):
        self.add_proxy(self.model, BasePaymentAddition.proxy_widgets)

    def validate_confirm(self):
        # FIXME: the kiwi view should export it's state and it shoul
        #        be used by default
        return bool(self.model.description and self.model.due_date and
                    self.model.value)

    def on_confirm(self):
        self.model.set_pending()
        self.model.base_value = self.model.value
        return self.model


class InPaymentAdditionDialog(BasePaymentAddition):

    def __init__(self, conn, till, model=None):
        """ This dialog is responsible to create additional payments with
        IInPayment facet.

        @param conn: a database connection
        @param till a L{stoqlib.domain.till.Till} object or None
        @param model: a L{stoqlib.domain.payment.payment.Payment} object or None
        """
        BasePaymentAddition.__init__(self, conn, model)
        self._till = till
        self.model.addFacet(IInPayment, connection=self.conn)
        self.model.till = self._till

    #
    # BaseEditor
    #

    def on_confirm(self):
        BasePaymentAddition.on_confirm(self)
        self._till.add_entry(self.model)
        return self.model


class OutPaymentAdditionDialog(BasePaymentAddition):

    def __init__(self, conn, model=None):
        """ This dialog is responsible to create additional payments with
        IOutPayment facet.

        @param conn: a database connection
        @param model: a L{stoqlib.domain.payment.payment.Payment} object or None
        """
        BasePaymentAddition.__init__(self, conn, model)
        self.model.addFacet(IOutPayment, connection=self.conn)
