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
""" Payments Renegotiation Wizard """

import datetime

from kiwi.currency import currency
from kiwi.datatypes import ValidationError
from kiwi.ui.objectlist import Column

from stoqlib.api import api
from stoqlib.domain.payment.renegotiation import PaymentRenegotiation
from stoqlib.domain.payment.group import PaymentGroup
from stoqlib.gui.base.wizards import WizardEditorStep, BaseWizard
from stoqlib.gui.search.searchcolumns import IdentifierColumn
from stoqlib.gui.wizards.salewizard import BaseMethodSelectionStep
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


#
# Wizard Steps
#

class PaymentRenegotiationPaymentListStep(BaseMethodSelectionStep,
                                          WizardEditorStep):
    gladefile = 'PaymentRenegotiationPaymentListStep'
    model_type = PaymentRenegotiation
    proxy_widgets = ('surcharge_value', 'discount_value', 'total')

    def __init__(self, store, wizard, model, groups):
        self.groups = groups
        WizardEditorStep.__init__(self, store, wizard, model)
        BaseMethodSelectionStep.__init__(self)

    def _setup_widgets(self):
        self.total.set_sensitive(False)
        self.subtotal.set_sensitive(False)

        client = self.groups[0].get_parent().client
        if client:
            self.client.prefill([(client.person.name, client)])
            self.client.select(client)
        self.client.set_sensitive(False)

        self.payment_list.set_columns(self._get_columns())
        payments = []
        for group in self.groups:
            group.renegotiation = self.model
            group.get_parent().set_renegotiated()
            payments.extend(group.get_pending_payments())

        assert len(payments)
        self.payment_list.add_list(payments)

        subtotal = 0
        for payment in payments:
            subtotal += payment.value
            payment.cancel()

        self._subtotal = subtotal
        self.subtotal.update(self._subtotal)

    def _get_columns(self):
        return [IdentifierColumn('identifier', title=('Payment #')),
                Column('description', title=_('Description'), data_type=str,
                       expand=True),
                Column('due_date', title=_('Due date'),
                       data_type=datetime.date, width=90),
                Column('status_str', title=_('Status'), data_type=str, width=80),
                Column('value', title=_('Value'), data_type=currency,
                       width=100)]

    def _update_totals(self):
        surcharge = self.model.surcharge_value
        discount = self.model.discount_value
        self.model.total = self._subtotal + surcharge - discount
        self.proxy.update('total')

    def _update_next_step(self, method):
        if method and method.method_name == 'money':
            self.wizard.enable_finish()
        else:
            self.wizard.disable_finish()

    #
    # WizardStep hooks
    #

    def post_init(self):
        self.model.group.clear_unused()
        self._update_next_step(self.pm_slave.get_selected_method())
        self.register_validate_function(self.wizard.refresh_next)
        self.force_validation()

        self.pm_slave.set_client(self.model.client, self.model.total)

    def setup_proxies(self):
        self._setup_widgets()
        self.proxy = self.add_proxy(self.model,
                                    PaymentRenegotiationPaymentListStep.proxy_widgets)
        self._update_totals()

    #
    #   Callbacks
    #

    def on_surcharge_value__validate(self, entry, value):
        if value < 0:
            return ValidationError(
                _('Surcharge must be greater than 0'))

    def on_discount_value__validate(self, entry, value):
        if value < 0:
            return ValidationError(
                _('Discount must be greater than 0'))
        if value >= self._subtotal:
            return ValidationError(
                _('Discount can not be greater than total amount'))

    def after_surcharge_value__changed(self, entry):
        self._update_totals()

    def after_discount_value__changed(self, entry):
        self._update_totals()


#
# Main wizard
#


class PaymentRenegotiationWizard(BaseWizard):
    size = (550, 400)
    title = _('Payments Renegotiation Wizard')

    def __init__(self, store, groups):
        self.groups = groups
        self.model = self._create_model(store)
        first = PaymentRenegotiationPaymentListStep(store, self, self.model, self.groups)
        BaseWizard.__init__(self, store, first, self.model)

    def need_create_payment(self):
        return self.get_total_amount() > 0

    def get_total_amount(self):
        return self.model.total

    def get_total_paid(self):
        return self.model.group.get_total_paid()

    def get_total_to_pay(self):
        return self.get_total_amount() - self.get_total_paid()

    def _create_model(self, store):
        value = 0  # will be updated in the first step.
        branch = api.get_current_branch(store)
        user = api.get_current_user(store)
        client = self.groups[0].get_parent().client
        # Set person as None to allow renegotiate payments without client.
        person = None
        if client:
            person = client.person
        group = PaymentGroup(payer=person,
                             store=store)
        model = PaymentRenegotiation(total=value,
                                     branch=branch,
                                     responsible=user,
                                     client=client,
                                     group=group,
                                     store=store)
        return model

    #
    # BaseWizard hooks
    #

    def finish(self):
        self.retval = True
        for payment in self.model.group.payments:
            payment.set_pending()
        self.close()
