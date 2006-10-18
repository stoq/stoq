# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006 Async Open Source <http://www.async.com.br>
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
## Author(s):   Evandro Vale Miquelito      <evandro@async.com.br>
##
##
"""Payment method management wizards"""

from decimal import Decimal

from kiwi.python import Settable
from kiwi.argcheck import argcheck
from sqlobject.dbconnection import Transaction

from stoqlib.gui.base.wizards import WizardEditorStep, BaseWizard
from stoqlib.gui.slaves.paymentmethodslave import (
    InstallmentsNumberSettingsSlave)
from stoqlib.domain.person import Person
from stoqlib.domain.interfaces import ICreditProvider
from stoqlib.domain.payment.destination import PaymentDestination
from stoqlib.domain.payment.methods import (CreditCardDetails,
                                            DebitCardDetails,
                                            CardInstallmentsStoreDetails,
                                            CardInstallmentsProviderDetails,
                                            PaymentMethodDetails,
                                            CardInstallmentSettings)
from stoqlib.lib.translation import stoqlib_gettext


_ = stoqlib_gettext


#
# Wizard Steps
#


class AbstractCreditCardStep(WizardEditorStep):
    gladefile = None
    proxy_widgets = None

    def __init__(self, conn, wizard, model, previous):
        self.model_type = type(model)
        WizardEditorStep.__init__(self, conn, wizard, model, previous)

    #
    # WizardStep hooks
    #

    def post_init(self):
        self.register_validate_function(self.wizard.refresh_next)
        self.force_validation()

    def has_next_step(self):
        return False


class CreditCardDetailsStep(AbstractCreditCardStep):
    gladefile = 'CreditCardDetailsStep'
    proxy_widgets = ('payment_day',
                     'closing_day')

    #
    # WizardStep hooks
    #

    def setup_slaves(self):
        ptype = self.wizard.get_method_details_type()
        if not ptype is CardInstallmentsStoreDetails:
            return
        slave = InstallmentsNumberSettingsSlave(self.conn, self.model)
        self.attach_slave('installments_number_holder', slave)

    def setup_proxies(self):
        self.add_proxy(self.model, CreditCardDetailsStep.proxy_widgets)


class DebitCardDetailsStep(AbstractCreditCardStep):
    gladefile = 'DebitCardDetailsStep'
    proxy_widgets = ('receive_days',)

    #
    # WizardStep hooks
    #

    def setup_proxies(self):
        self.add_proxy(self.model, DebitCardDetailsStep.proxy_widgets)


class PMDetailsGeneralDataStep(WizardEditorStep):
    gladefile = 'PMDetailsGeneralDataStep'
    model_type = None
    general_widgets = ('destination',
                       'commission')
    payment_type_widgets = ('payment_type',)
    proxy_widgets = general_widgets + payment_type_widgets

    def __init__(self, conn, wizard, model):
        self.model_type = type(model)
        WizardEditorStep.__init__(self, conn, wizard, model)
        if self.wizard.edit_mode:
            self.payment_type.set_sensitive(False)

    def _setup_combos(self):
        table = PaymentDestination
        self.destinations = [(p.description, p)
                        for p in table.select(connection=self.conn)]
        self.destination.prefill(self.destinations, sort=True)
        payment_types = [DebitCardDetails, CreditCardDetails,
                         CardInstallmentsStoreDetails,
                         CardInstallmentsProviderDetails]
        self.payment_types = [(p.get_description(), p) for p in payment_types]
        self.payment_type.prefill(self.payment_types, sort=True)

    #
    # WizardStep hooks
    #

    def post_init(self):
        self.register_validate_function(self.wizard.refresh_next)
        self.force_validation()

    def next_step(self):
        args = [self.conn, self.wizard, self.model, self]
        ptype = self.wizard.get_method_details_type()
        if ptype is DebitCardDetails:
            return DebitCardDetailsStep(*args)
        return CreditCardDetailsStep(*args)

    def setup_proxies(self):
        self._setup_combos()
        if self.wizard.edit_mode:
            proxy_widgets = PMDetailsGeneralDataStep.general_widgets
        else:
            proxy_widgets = PMDetailsGeneralDataStep.proxy_widgets
        self.add_proxy(self.model, proxy_widgets)
        if self.wizard.edit_mode:
            return
        # XXX dirty hack, kiwi select_item_by_data is not updating the model
        destination = self.destinations[0][1]
        self.destination.select_item_by_data(destination)
        self.model.destination = destination
        payment_type = self.payment_types[0][1]
        self.payment_type.select_item_by_data(payment_type)
        self.model.payment_type = payment_type

#
# Main wizard
#


class PaymentMethodDetailsWizard(BaseWizard):
    size = (350, 200)
    # XXX I don't know why but pyflakes thinks that Person and
    # ICreditProvider are not imported in this module if I use them with
    # argcheck
    provider_table = Person.getAdapterClass(ICreditProvider)

    @argcheck(Transaction, provider_table, PaymentMethodDetails)
    def __init__(self, conn, credprovider, model=None):
        self.credprovider = credprovider
        title = self.get_title(model)
        self.edit_mode = model is not None
        model = model or self._get_model()
        first_step = PMDetailsGeneralDataStep(conn, self, model)
        BaseWizard.__init__(self, conn, first_step, model, title=title,
                            edit_mode=self.edit_mode)

    def _get_model(self):
        settings = Settable(payment_day=1, closing_day=1)
        return Settable(destination=None, provider=None,
                        payment_type=None, installment_settings=settings,
                        max_installments_number=1, receive_days=0,
                        commission=Decimal(0))

    def get_method_details_type(self):
        if self.edit_mode:
            return type(self.model)
        return self.model.payment_type

    def get_title(self, model=None):
        if model:
            return _("Edit Payment Type")
        return _("Add Payment Type")

    #
    # WizardStep hooks
    #

    def finish(self):
        if self.edit_mode:
            self.retval = self.model
        else:
            klass = self.model.payment_type
            kwargs = dict(connection=self.conn,
                          destination=self.model.destination,
                          provider=self.credprovider,
                          commission=self.model.commission)
            payment_day = self.model.installment_settings.payment_day
            closing_day = self.model.installment_settings.closing_day
            creditcard_kwargs = dict(payment_day=payment_day,
                                     closing_day=closing_day)
            if klass is DebitCardDetails:
                kwargs['receive_days'] = self.model.receive_days
            else:
                settings = CardInstallmentSettings(connection=self.conn,
                                                   **creditcard_kwargs)
                kwargs['installment_settings'] = settings
                if klass is CardInstallmentsStoreDetails:
                    value = self.model.max_installments_number
                    kwargs['max_installments_number'] = value
            self.retval = klass(**kwargs)
        self.close()
