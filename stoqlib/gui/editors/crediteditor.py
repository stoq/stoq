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
""" Editor for credit payments"""

import collections

from kiwi.currency import currency
from kiwi.datatypes import ValidationError
from kiwi.python import Settable
from kiwi.ui.forms import PriceField, TextField

from stoqlib.api import api
from stoqlib.domain.payment.group import PaymentGroup
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.domain.payment.payment import Payment
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.lib.dateutils import localtoday
from stoqlib.lib.decorators import cached_property
from stoqlib.lib.translation import stoqlib_gettext as _


class CreditEditor(BaseEditor):
    model_type = Settable
    model_name = _('Credit Transaction')

    confirm_widgets = ['description', 'value']

    @cached_property()
    def fields(self):
        return collections.OrderedDict(
            description=TextField(_('Description'), proxy=True, mandatory=True),
            value=PriceField(_('Value'), proxy=True, mandatory=True),
        )

    def __init__(self, store, client, model=None):
        self.client = store.fetch(client)
        assert self.client
        BaseEditor.__init__(self, store, model)

    def create_model(self, store):
        return Settable(description=u'', value=currency(0))

    def _create_payment(self):
        group = PaymentGroup()
        group.payer = self.client.person

        method = PaymentMethod.get_by_name(self.store, u'credit')
        branch = api.get_current_branch(self.store)

        if self.model.value < 0:
            payment_type = Payment.TYPE_IN
        else:
            payment_type = Payment.TYPE_OUT

        # Set status to PENDING now, to avoid calling set_pending on
        # on_confirm for payments that shoud not have its status changed.
        payment = Payment(open_date=localtoday(),
                          branch=branch,
                          status=Payment.STATUS_PENDING,
                          description=self.model.description,
                          value=abs(self.model.value),
                          base_value=abs(self.model.value),
                          due_date=localtoday(),
                          method=method,
                          group=group,
                          category=None,
                          payment_type=payment_type,
                          bill_received=False)
        payment.pay()

        return payment

    def validate_confirm(self):
        return bool(self.model.description and
                    self.model.value)

    def on_confirm(self):
        self.retval = self._create_payment()

    def on_value__validate(self, widget, newvalue):
        if newvalue == 0:
            return ValidationError(_(u'Value must be different from zero.'))
        if self.client.credit_account_balance + newvalue < 0:
            return ValidationError(_(u'Client credit cannot be negative.'))
