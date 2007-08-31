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

from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.domain.interfaces import IOutPayment
from stoqlib.domain.payment.payment import Payment

_ = stoqlib_gettext


class PaymentAdditionDialog(BaseEditor):
    gladefile = "PaymentAdditionDialog"
    model_type = Payment
    title = _(u"Payment")
    proxy_widgets = ['value',
                     'description',
                     'due_date']

    def __init__(self, conn, model=None):
        """
        @param conn: a database connection
        @param model: a L{stoqlib.domain.payment.payment.Payment} object or None
        """
        BaseEditor.__init__(self, conn, model)

    #
    # BaseEditor hooks
    #

    def create_model(self, trans):
        payment = Payment(open_date=datetime.date.today(),
                          description='',
                          value=currency(0),
                          base_value=currency(0),
                          due_date=None,
                          method=None,
                          group=None,
                          till=None,
                          destination=None,
                          connection=trans)
        payment.addFacet(IOutPayment, connection=trans)
        return payment

    def on_due_date__activate(self, date):
        self.main_dialog.confirm()

    def setup_proxies(self):
        self.add_proxy(self.model, PaymentAdditionDialog.proxy_widgets)

    def validate_confirm(self):
        # FIXME: the kiwi view should export it's state and it shoul
        #        be used by default
        return bool(self.model.description and self.model.due_date and
                    self.model.value)

    def on_confirm(self):
        self.model.set_pending()
        self.model.base_value = self.model.value
        return self.model
