# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2011 Async Open Source <http://www.async.com.br>
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
"""Editors for payment method management.

This module contains the following editors and slaves:

- :obj:`PaymentMethodEditor`: A generic editor for all payments.
- :obj:`CardPaymentMethodEditor`: A specialized editor for the card payment
  method. This editor uses the following slaves:

  - :obj:`PaymentMethodEditor`: see above
  - :obj:`ProviderListSlave`: the available CreditProviders
  - :obj:`CardDeviceListSlave`: the available CardPaymentDevices

- :obj:`CardDeviceEditor`: the editor used by CardDeviceListSlave. It uses
  the slave:

  - :obj:`CardOperationCostListSlave`: all the costs generated when using this
    device

- :obj:`CardOperationCostEditor`: the editor used by CardOperationCostListSlave
- :obj:`CreditProviderEditor`: editor for the
  :obj:`stoqlib.domain.payment.card.CreditProvider`
"""

import collections
from decimal import Decimal

import gtk

from kiwi.currency import currency
from kiwi.datatypes import ValidationError
from kiwi import ValueUnset
from kiwi.ui.objectlist import Column
from kiwi.ui.forms import ChoiceField, IntegerField

from stoqlib.api import api
from stoqlib.domain.account import Account
from stoqlib.domain.payment.card import (CreditProvider,
                                         CreditCardData,
                                         CardPaymentDevice,
                                         CardOperationCost)
from stoqlib.domain.payment.method import PaymentMethod
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.base.lists import ModelListSlave
from stoqlib.gui.editors.baseeditor import BaseEditorSlave, BaseEditor
from stoqlib.lib.decorators import cached_property
from stoqlib.lib.formatters import get_formatted_percentage
from stoqlib.lib.message import yesno, info
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


#
#   Editors
#

class PaymentMethodEditor(BaseEditor):
    """A generic editor for payment methods.

    This uses the slave :obj:`PaymentMethodSlave` to edit the generic
    information for the payment method.

    If some method have specific information, another editor should be
    implemented and still use the :obj:`PaymentMethodSlave`
    """
    model_name = _('Payment Method')
    gladefile = 'HolderTemplate'
    model_type = PaymentMethod

    def setup_slaves(self):
        slave = PaymentMethodSlave(self.store, self.model)
        self.attach_slave('place_holder', slave)


class CardPaymentMethodEditor(BaseEditor):
    """Specific editor for card payment method.

    This is organized in 3 different tabs, each with one slave:

    * :obj:`PaymentMethodSlave`
    * :obj:`ProviderListSlave`
    * :obj:`CardDeviceListSlave`
    """
    model_name = _('Payment Method')
    gladefile = 'CardMethodEditor'
    model_type = PaymentMethod

    def setup_slaves(self):
        slave = PaymentMethodSlave(self.store, self.model)
        self.attach_slave('method_holder', slave)

        slave = ProviderListSlave(store=self.store)
        self.attach_slave('providers_holder', slave)

        slave = CardDeviceListSlave(store=self.store)
        self.attach_slave('devices_holder', slave)


class CardDeviceEditor(BaseEditor):
    """Edits the details about a
    :obj:`card device <stoqlib.domain.payment.card.CardPaymentDevice>`
    """
    model_name = _('Card Device')
    gladefile = 'CardDeviceEditor'
    model_type = CardPaymentDevice
    # TODO: Add monthly_cost, maybe use formfields
    proxy_widgets = ['description']
    confirm_widgets = ['description']
    size = (600, 300)

    def create_model(self, store):
        return CardPaymentDevice(store=store)

    def setup_slaves(self):
        slave = CardOperationCostListSlave(self.store, self.model,
                                           reuse_store=True)
        self.attach_slave('cost_holder', slave)

    def setup_proxies(self):
        self.add_proxy(self.model, self.proxy_widgets)


class _TemporaryOperationCost(object):
    """Temporary object used to edit.

    This is used to prevent a few issues with the database when validating,
    since the orm may commit the changes made on the real model, even though
    they are not valid yet.
    """

    properties = ['device', 'provider', 'card_type', 'installment_start',
                  'installment_end', 'payment_days', 'fee', 'fare']

    def __init__(self, model):
        self.real_model = model
        for prop in self.properties:
            setattr(self, prop, getattr(model, prop))

    def save(self):
        """Save the changes made to self to the actual database model
        """
        for prop in self.properties:
            setattr(self.real_model, prop, getattr(self, prop))


class CardOperationCostEditor(BaseEditor):
    """Edits the details about a
    :obj:`stoqlib.domain.payment.card.CardOperationCost`
    """
    model_name = _('Card Device Cost')
    gladefile = 'CardOperationCostEditor'
    model_type = _TemporaryOperationCost
    proxy_widgets = ['fee', 'fare', 'installment_start', 'installment_end',
                     'payment_days', 'provider', 'card_type']
    confirm_widgets = ['fee', 'fare', 'installment_start', 'installment_end',
                       'payment_days']

    def __init__(self, store, model, device):
        self.device = device
        if model:
            assert model.device == device
            model = _TemporaryOperationCost(model)

        card_method = store.find(PaymentMethod, method_name=u'card').one()
        self.max_installments = card_method.max_installments

        BaseEditor.__init__(self, store, model)

    def create_model(self, store):
        provider = CreditProvider.get_card_providers(store).any()
        real_model = CardOperationCost(provider=provider, device=self.device,
                                       store=self.store)
        return _TemporaryOperationCost(real_model)

    def _setup_widgets(self):
        # Set a default provider, otherwise, if the user does not change the
        # combo, the provider may not be set (bug in kiwi)
        providers = CreditProvider.get_card_providers(self.store)
        self.provider.prefill(api.for_combo(providers))

        types = [(value, key) for key, value in CreditCardData.types.items()]
        self.card_type.prefill(types)

        # Set values to the ones of the model
        self.installment_start.set_value(self.model.installment_start)
        self.installment_end.set_value(self.model.installment_end)

        self.set_installment_limits()

    def setup_proxies(self):
        self._setup_widgets()
        self.add_proxy(self.model, self.proxy_widgets)

    def on_confirm(self):
        self.model.save()
        self.retval = self.model.real_model

    def has_installments(self):
        """If the currenct selected card type have installments
        """
        inst_types = [CreditCardData.TYPE_CREDIT_INSTALLMENTS_STORE,
                      CreditCardData.TYPE_CREDIT_INSTALLMENTS_PROVIDER]
        return self.model.card_type in inst_types

    def set_installment_limits(self):
        has_installments = self.has_installments()
        # Use set_editable instead of set_sensitive so that validation still
        # works
        self.installment_start.set_editable(has_installments)
        self.installment_end.set_editable(has_installments)

        if not has_installments:
            self.installment_start.set_value(1)
            self.installment_end.set_value(1)
            self.installment_end.get_adjustment().set_upper(1)
            self.installment_start.get_adjustment().set_upper(1)
        else:
            self.installment_end.get_adjustment().set_upper(
                self.max_installments)
            self.installment_start.get_adjustment().set_upper(
                self.max_installments)

    # Editing the start/end could invalidate the other value of the range, so
    # after it changes we force the other value validation
    def on_installment_start__changed(self, widget):
        self.installment_end.validate(force=True)

    def on_installment_end__changed(self, widget):
        self.installment_start.validate(force=True)

    def on_card_type__changed(self, widget):
        self.set_installment_limits()

        self.installment_start.validate(force=True)
        self.installment_end.validate(force=True)

    def on_provider__changed(self, widget):
        self.installment_start.validate(force=True)
        self.installment_end.validate(force=True)

    def _validate_range(self, start, end):
        if ValueUnset in [start, end]:
            return

        if start > end:
            return ValidationError(_('Installments start should be lower '
                                     'or equal installments end'))

        if not CardOperationCost.validate_installment_range(
                device=self.model.device,
                provider=self.model.provider, card_type=self.model.card_type,
                start=start, end=end, ignore=self.model.real_model.id,
                store=self.store):
            return ValidationError(_('The installments range is conflicting '
                                     'with another configuration'))

    def on_installment_start__validate(self, widget, start):
        end = self.installment_end.read()
        return self._validate_range(start, end)

    def on_installment_end__validate(self, widget, end):
        start = self.installment_start.read()
        return self._validate_range(start, end)


class CreditProviderEditor(BaseEditor):
    """Editor for :obj:`stoqlib.domain.payment.card.CreditProvider` details
    """
    model_type = CreditProvider
    gladefile = 'CreditProviderEditor'
    proxy_widgets = ['provider_id', 'short_name',
                     'max_installments', 'default_device', 'open_contract_date']

    def setup_proxies(self):
        self._setup_widgets()
        self.proxy = self.add_proxy(self.model,
                                    CreditProviderEditor.proxy_widgets)

    def _setup_widgets(self):
        """ Populate device widgets
        """
        devices = CardPaymentDevice.get_devices(self.store)
        self.default_device.prefill(api.for_combo(devices,
                                                  empty=_(u"No device")))

    def create_model(self, store):
        return CreditProvider(store=store)

    def on_max_installments__validate(self, widget, value):
        if value <= 0:
            return ValidationError(_("The max installments must be greater than zero."))


class CardPaymentDetailsEditor(BaseEditor):
    """Editor for :obj: `stoqlib.domain.payment.CreditCardData`
    """
    model_type = CreditCardData

    @cached_property()
    def fields(self):
        device_values = api.for_combo(
            CardPaymentDevice.get_devices(self.store))
        provider_values = api.for_combo(
            CreditProvider.get_card_providers(self.store))

        return collections.OrderedDict(
            device=ChoiceField(_('Device'), proxy=True, mandatory=True,
                               values=device_values),
            provider=ChoiceField(_('Provider'), proxy=True, mandatory=True,
                                 values=provider_values),
            auth=IntegerField(_('Authorization'), proxy=True, mandatory=True)
        )

    def on_confirm(self):
        self.model.update_card_data(device=self.model.device,
                                    provider=self.model.provider,
                                    card_type=self.model.card_type,
                                    installments=self.model.installments)


#
#   Slaves
#

class PaymentMethodSlave(BaseEditorSlave):
    """Slave for editing generic payment method details
    """
    model_name = _('Payment Method')
    gladefile = 'PaymentMethodEditor'
    model_type = PaymentMethod
    proxy_widgets = ('account',
                     'max_installments',
                     'penalty',
                     'daily_interest')

    def _setup_widgets(self):
        accounts = self.store.find(Account)
        self.account.prefill(api.for_combo(
            accounts, attr='long_description'))
        self.account.select(self.model.destination_account)

    #
    # BaseEditor Hooks
    #

    def setup_proxies(self):
        self._setup_widgets()
        self.add_proxy(self.model, self.proxy_widgets)

    def on_confirm(self):
        self.model.destination_account = self.account.get_selected()

    #
    #   Validators
    #

    def on_daily_interest__validate(self, widget, value):
        if value < 0:
            return ValidationError(_(u'The value must be positive.'))

    def on_penalty__validate(self, widget, value):
        if value < 0:
            return ValidationError(_(u'The value must be positive.'))

    def on_max_installments__validate(self, widget, value):
        if value <= 0:
            return ValidationError(_(u'The value must be positive.'))


class ProviderListSlave(ModelListSlave):
    """Slave listing all :obj:`stoqlib.domain.payment.card.CreditProvider` objects
    """
    model_type = CreditProvider
    editor_class = CreditProviderEditor

    columns = [
        Column('short_name', title=_('Name'),
               data_type=str, expand=True),
        Column('max_installments', title=_('Max Installments'), data_type=int)
    ]

    def populate(self):
        providers = self.store.find(CreditProvider)
        return providers.order_by(CreditProvider.short_name)

    def remove_item(self, provider):
        if self.store.find(CardOperationCost, provider=provider).any():
            info(_("You can not remove this provider.\n"
                   "It is being used in card device."))
            return False
        elif self.store.find(CreditCardData, provider=provider).any():
            info(_("You can not remove this provider.\n"
                   "You already have payments using this provider."))
            return False

        msg = _('Do you want remove %s?' % provider.short_name)
        remove = yesno(msg, gtk.RESPONSE_NO, _('Remove'), _("Cancel"))
        if remove:
            self.delete_model(provider, self.store)
            self.remove_list_item(provider)
        return False


class CardDeviceListSlave(ModelListSlave):
    """Slave listing all :obj:`stoqlib.domain.payment.card.CardPaymentDevice` objects
    """
    model_type = CardPaymentDevice
    editor_class = CardDeviceEditor

    columns = [
        Column('description', title=_('Description'),
               data_type=str, expand=True),
    ]

    def populate(self):
        devices = CardPaymentDevice.get_devices(self.store)
        return devices.order_by(CardPaymentDevice.description)

    def remove_item(self, device):
        providers = self.store.find(CreditProvider, default_device=device).count()
        if providers > 0:
            info(_("Can not remove this device.\n"
                   "It is being used as default device in %s credit provider(s)."
                   % providers))
            return False
        msg = _('Removing this device will also remove all related costs.')
        remove = yesno(msg, gtk.RESPONSE_NO, _('Remove'), _("Keep device"))
        if remove:
            device.delete(device.id, self.store)
            self.remove_list_item(device)
        return False


class CardOperationCostListSlave(ModelListSlave):
    """Slave listing all :obj:`stoqlib.domain.payment.card.CardOperationCost`
    for a given :obj:`stoqlib.domain.payment.card.CardOperationCost`
    """
    model_type = CardOperationCost

    columns = [
        Column('description', title=_('Description'), data_type=str,
               expand=True),
        Column('installment_range_as_string', title=_('Installments'),
               data_type=str),
        Column('payment_days', title=_('Days'), data_type=int),
        # Translators: Fee is Taxa in pt_BR
        Column('fee', title=_('Fee'), data_type=Decimal,
               format_func=get_formatted_percentage),
        # Translators: Fare is Tarifa in pt_BR
        Column('fare', title=_('Fare'), data_type=currency),
    ]

    def __init__(self, store, device, reuse_store=False):
        self.device = device
        ModelListSlave.__init__(self, store=store, reuse_store=reuse_store)

    def populate(self):
        return self.device.get_all_costs()

    def remove_item(self, item):
        self.remove_list_item(item)
        self._delete_model(item)
        return False

    def run_editor(self, store, model):
        device = store.fetch(self.device)
        return self.run_dialog(CardOperationCostEditor, store=store,
                               model=model, device=device)


def test():  # pragma nocover
    creator = api.prepare_test()
    method = PaymentMethod.get_by_name(creator.store, u'card')
    retval = run_dialog(CardPaymentMethodEditor, None, creator.store, method)
    creator.store.confirm(retval)


if __name__ == '__main__':  # pragma nocover
    test()
