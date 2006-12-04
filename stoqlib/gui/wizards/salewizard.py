# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005, 2006 Async Open Source <http://www.async.com.br>
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
""" Sale wizard definition """

from decimal import Decimal

from kiwi.utils import gsignal
from kiwi.ui.widgets.list import Column, SummaryLabel
from kiwi.ui.wizard import WizardStep
from kiwi.datatypes import currency
from kiwi.argcheck import argcheck
from kiwi.python import Settable

from stoqlib.database.runtime import StoqlibTransaction
from stoqlib.lib.message import warning
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.validators import get_formatted_price
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.drivers import (print_cheques_for_payment_group,
                                 check_virtual_printer_for_current_station)
from stoqlib.lib.defaults import METHOD_MONEY, METHOD_MULTIPLE
from stoqlib.gui.base.wizards import WizardEditorStep, BaseWizard
from stoqlib.gui.base.lists import AdditionListSlave
from stoqlib.gui.wizards.abstractwizard import (AbstractSaleWizard,
                                                AbstractSalesPersonStep)
from stoqlib.gui.slaves.paymentslave import (CheckMethodSlave, BillMethodSlave,
                                        CardMethodSlave,
                                        FinanceMethodSlave)
from stoqlib.domain.payment.methods import get_active_pm_ifaces
from stoqlib.domain.payment.payment import AbstractPaymentGroup
from stoqlib.domain.sale import Sale, GiftCertificateOverpaidSettings
from stoqlib.domain.sellable import ASellable
from stoqlib.domain.giftcertificate import (GiftCertificate,
                                            get_volatile_gift_certificate)
from stoqlib.domain.interfaces import (ICheckPM, ICardPM, IBillPM,
                                       IFinancePM, ISellable,
                                       IMultiplePM, IMoneyPM,
                                       IGiftCertificatePM)
_ = stoqlib_gettext


#
# Wizard Steps
#

class PaymentMethodStep(WizardEditorStep):
    gladefile = 'PaymentMethodStep'
    model_type = Sale
    slave_holder = 'method_holder'

    slaves_info = ((ICheckPM, CheckMethodSlave),
                   (IBillPM, BillMethodSlave),
                   (ICardPM, CardMethodSlave),
                   (IFinancePM, FinanceMethodSlave))

    def __init__(self, wizard, previous, conn, model,
                 outstanding_value=currency(0)):
        # A dictionary for payment method informaton. Each key is a
        # PaymentMethod adapter and its value is a tuple where the first
        # element is a payment method interface and the second one is the
        # slave class
        self.method_dict = {}
        # A cache for instantiated slaves
        self.slaves_dict = {}
        self.method_slave = None

        self.outstanding_value = outstanding_value
        self.group = wizard.payment_group
        self.renegotiation_mode = outstanding_value > currency(0)
        WizardEditorStep.__init__(self, conn, wizard, model, previous)
        self.conn.savepoint('payment')

        self.handler_block(self.method_combo, 'changed')
        self._setup_combo()
        self.handler_unblock(self.method_combo, 'changed')

        self._update_payment_method_slave()

    def _set_method_slave(self, slave_class, slave_args):
        if not self.slaves_dict.has_key(slave_class):
            slave = slave_class(*slave_args)
            self.slaves_dict[slave_class] = slave
            if slave_class is BillMethodSlave:
                slave.bank_label.hide()
                slave.bank_combo.hide()
        else:
            slave = self.slaves_dict[slave_class]
        self.method_slave = slave

    def _update_payment_method(self, iface):
        if self.renegotiation_mode:
            return
        self.group.set_method(iface)

    def _update_payment_method_slave(self):
        selected = self.method_combo.get_selected_data()
        slave_args = (self.wizard, self, self.conn, self.model,
                      selected, self.outstanding_value)
        if not self.method_dict.has_key(selected):
            raise ValueError('Invalid payment method type: %s'
                             % type(selected))
        iface, slave_class = self.method_dict[selected]
        self._update_payment_method(iface)
        self._set_method_slave(slave_class, slave_args)
        if self.get_slave(self.slave_holder):
            self.detach_slave(self.slave_holder)
        self.attach_slave(self.slave_holder, self.method_slave)

    def _setup_combo(self):
        active_pm_ifaces = get_active_pm_ifaces()
        base_method = sysparam(self.conn).BASE_PAYMENT_METHOD
        combo_items = []
        for iface, slave_class in PaymentMethodStep.slaves_info:
            if not iface in active_pm_ifaces:
                continue
            method = iface(base_method)
            if method.is_active:
                self.method_dict[method] = iface, slave_class
                combo_items.append((method.description, method))
        self.method_combo.prefill(combo_items)


    #
    # WizardStep hooks
    #

    def validate_step(self):
        self.method_slave.finish()
        return True

    def has_next_step(self):
        return False

    def post_init(self):
        self.method_combo.grab_focus()
        if self.method_slave:
            self.method_slave.update_view()

    #
    # Kiwi callbacks
    #

    def on_method_combo__changed(self, *args):
        self.conn.rollback('payment')
        self._update_payment_method_slave()
        self.conn.savepoint('payment')

class SaleRenegotiationOutstandingStep(WizardEditorStep):
    gladefile = 'SaleRenegotiationOutstandingStep'
    model_type = Sale

    def __init__(self, wizard, previous, conn, sale, outstanding_value):
        self.outstanding_value = outstanding_value
        self.sale = sale
        self.group = wizard.payment_group
        self._is_last = True
        WizardEditorStep.__init__(self, conn, wizard, model=sale,
                                  previous=previous)
        self.register_validate_function(self.wizard.refresh_next)
        self._setup_widgets()

    def _setup_widgets(self):
        text = (_('Select method of payment for the %s outstanding value')
                % get_formatted_price(self.outstanding_value))
        self.header_label.set_text(text)
        self.header_label.set_size('large')
        self.header_label.set_bold(True)

    #
    # WizardStep hooks
    #


    def next_step(self):
        if self.other_methods_check.get_active():
            method = METHOD_MULTIPLE
        else:
            method = METHOD_MONEY
            self.wizard.setup_cash_payment(self.outstanding_value)

        # FIXME: Use method for something
        method

        if self._is_last:
            # finish the wizard
            return
        return PaymentMethodStep(self.wizard, self, self.conn, self.sale,
                                 self.outstanding_value)

    def post_init(self):
        self.wizard.payment_group.clear_preview_payments()
        self.cash_check.grab_focus()
        self.wizard.enable_finish()

    #
    # Callbacks
    #

    def on_cash_check__toggled(self, *args):
        self._is_last = True
        self.wizard.enable_finish()

    def on_other_methods_check__toggled(self, *args):
        self._is_last = False
        self.wizard.disable_finish()


class SaleRenegotiationOverpaidStep(WizardEditorStep):
    gladefile = 'SaleRenegotiationOverpaidStep'
    model_type = Settable
    proxy_widgets = ('certificate_number',)
    gsignal('on-validate-step', object)

    @argcheck(BaseWizard, WizardStep, StoqlibTransaction, Sale,
              AbstractPaymentGroup, Decimal)
    def __init__(self, wizard, previous, conn, sale, payment_group,
                 overpaid_value):
        self.overpaid_value = overpaid_value
        self.sale = sale
        self.payment_group = payment_group
        WizardEditorStep.__init__(self, conn, wizard, previous=previous)
        self.register_validate_function(self.refresh_next)

    def _setup_widgets(self):
        if not sysparam(self.conn).RETURN_MONEY_ON_SALES:
            self.return_check.set_sensitive(False)
        certificate = sysparam(self.conn).DEFAULT_GIFT_CERTIFICATE_TYPE
        description = certificate.base_sellable_info.description
        text = _('Create a <u>%s</u> with this value') % description
        self.certificate_label.set_text(text)
        header_text = (_('There is %s overpaid') %
                       get_formatted_price(self.overpaid_value))
        self.header_label.set_text(header_text)
        self.header_label.set_size('large')
        self.header_label.set_bold(True)

    def refresh_next(self, validation_value):
        if (self.certificate_check.get_active()
            and not self.model.number):
            validation_value = False
        self.wizard.refresh_next(validation_value)

    def _create_gift_certificate_settings(self, rtype, value, number=None):
        settings = GiftCertificateOverpaidSettings()
        settings.renegotiation_type = rtype
        settings.renegotiation_value = value
        settings.gift_certificate_number = number
        return settings

    #
    # BaseEditorSlave hooks
    #

    def create_model(self, conn):
        return get_volatile_gift_certificate()

    def setup_proxies(self):
        self._setup_widgets()
        klass = SaleRenegotiationOverpaidStep
        self.proxy = self.add_proxy(self.model, klass.proxy_widgets)

    #
    # WizardStep hooks
    #

    def validate_step(self):
        number = self.model.number
        if ASellable.check_barcode_exists(number):
            msg = _(u"The barcode %s already exists") % number
            self.certificate_number.set_invalid(msg)
            return False

        value = self.overpaid_value
        if self.certificate_check.get_active():
            rtype = GiftCertificateOverpaidSettings.TYPE_GIFT_CERTIFICATE
            obj = self._create_gift_certificate_settings(rtype, value,
                                                         number)
        else:
            rtype = GiftCertificateOverpaidSettings.TYPE_RETURN_MONEY
            obj = self._create_gift_certificate_settings(rtype, value)
        self.emit('on-validate-step', obj)
        return True

    def has_next_step(self):
        return False

    def post_init(self):
        self._update_widgets()
        self.certificate_number.grab_focus()

    #
    # Callbacks
    #

    def _update_widgets(self):
        can_return_money = self.return_check.get_active()
        self.certificate_number.set_sensitive(not can_return_money)
        self.force_validation()

    def after_certificate_number__changed(self, *args):
        self._update_widgets()

    def on_certificate_check__toggled(self, *args):
        self._update_widgets()

    def on_return_check__toggled(self, *args):
        self._update_widgets()


class GiftCertificateSelectionStep(WizardEditorStep):
    gladefile = 'GiftCertificateSelectionStep'
    model_type = Settable
    proxy_widgets = ('certificate_number',)

    def __init__(self, wizard, previous, conn, sale):
        self.sale = sale
        self.sale_total = self.sale.get_total_sale_amount()
        self.group = wizard.payment_group
        WizardEditorStep.__init__(self, conn, wizard, previous=previous)

    def _setup_widgets(self):
        self.header_label.set_size('large')
        self.header_label.set_bold(True)
        adapter_class = GiftCertificate.getAdapterClass(ISellable)
        sellables = adapter_class.get_sold_sellables(self.conn)
        items = [(sellable.get_short_description(), sellable)
                     for sellable in sellables]
        self.certificate_number.prefill(items)

    def _get_columns(self):
        return [Column('code', title=_('Number'), data_type=str, width=90),
                Column('description', title=_('Description'), data_type=str,
                       expand=True, searchable=True),
                Column('price', title=_('Price'), data_type=currency,
                       width=90)]

    def _update_total(self, *args):
        self.summary.update_total()
        gift_total = currency(
            sum([gift.price for gift in self.slave.klist], currency(0)))
        if gift_total == self.sale_total:
            text = ''
            value = ''
            self.wizard.enable_finish()
        else:
            value = self.sale_total - gift_total
            if gift_total < self.sale_total:
                text = _('Outstanding:')
            else:
                text = _('Overpaid:')
                value = -value
            value = get_formatted_price(value)
            self.wizard.disable_finish()

        self.difference_label.set_text(text)
        self.difference_value_label.set_text(value)

    def _get_certificate_by_code(self, code):
        certificate = GiftCertificate.iselectOneBy(ISellable, code=code,
                                                   connection=self.conn)
        if certificate is None:
            self.certificate_number.set_invalid(
                _("The gift certificate with code '%s' doesn't exists.") % code)
        return certificate

    def _update_widgets(self):
        has_gift_certificate = self.certificate_number.get_text() != ''
        self.add_button.set_sensitive(has_gift_certificate)
        if len(self.slave.klist):
            self.wizard.enable_next()
        else:
            self.wizard.disable_next()

    def _add_item(self):
        certificate = self.proxy.model and self.proxy.model.number
        self.add_button.set_sensitive(False)
        if not certificate:
            code = self.certificate_number.get_text()
            certificate = self._get_certificate_by_code(code)
            if not certificate:
                return
        if certificate in self.slave.klist[:]:
            msg = (_("The gift certificate '%s' was already added to the"
                     "list") % certificate.get_short_description())
            self.certificate_number.set_invalid(msg)
            return
        item = certificate or self.model.number
        self.slave.klist.append(item)
        # As we have a selection extended mode for kiwi list, we
        # need to unselect everything before select the new instance.
        self.slave.klist.unselect_all()
        self.slave.klist.select(item)
        self.certificate_number.set_text('')
        self._update_total()

    #
    # BaseEditorSlave hooks
    #

    def create_model(self, conn):
        return get_volatile_gift_certificate()

    def setup_proxies(self):
        self._setup_widgets()
        self.proxy = self.add_proxy(
            self.model, GiftCertificateSelectionStep.proxy_widgets)

    def setup_slaves(self):
        self.slave = AdditionListSlave(self.conn,
                                       self._get_columns(),
                                       klist_objects=[])
        self.slave.hide_edit_button()
        self.slave.hide_add_button()
        self.slave.connect('after-delete-items', self.after_delete_items)
        self.summary = SummaryLabel(klist=self.slave.klist,
                                    column='price',
                                    label=_('<b>Total:</b>'),
                                    value_format="<b>%s</b>")
        self.summary.show()
        self.slave.list_vbox.pack_start(self.summary, expand=False)
        self.attach_slave('list_holder', self.slave)

    #
    # WizardStep hooks
    #

    def next_step(self):
        if not len(self.slave.klist):
            raise ValueError('You should have at least one gift certificate '
                             'selected at this point')
        gift_total = 0
        for certificate in self.slave.klist:
            self.wizard.gift_certificates.append(certificate)
            gift_total += certificate.price
        if gift_total == self.sale_total:
            # finish the wizard
            return
        elif self.sale_total > gift_total:
            outstanding_value = self.sale_total - gift_total
            return SaleRenegotiationOutstandingStep(
                self.wizard, self, self.conn, self.sale, outstanding_value)
        else:
            overpaid_value = gift_total - self.sale_total
            step = SaleRenegotiationOverpaidStep(
                self.wizard, self, self.conn, self.sale, self.group,
                overpaid_value)
            step.connect('on-validate-step',
                         self.wizard.set_gift_certificate_settings)
            return step

    def post_init(self):
        # Reset this field each time users go back to this step
        self.wizard.gift_certificate_settings = None

        self.register_validate_function(self.wizard.refresh_next)
        self._update_total()
        self.certificate_number.grab_focus()
        self._update_widgets()

    #
    # Callbacks
    #

    def on_add_button__clicked(self, *args):
        self._add_item()

    def on_certificate_number__activate(self, *args):
        if not self.add_button.get_property('sensitive'):
            return
        self._add_item()

    def on_certificate_number__changed(self, *args):
        self._update_widgets()

    def after_delete_items(self, *args):
        self._update_total()
        self._update_widgets()

class SalesPersonStep(AbstractSalesPersonStep):
    """A wizard step used when confirming a sale order """

    def _update_next_step(self, pm_iface):
        if pm_iface is IMoneyPM:
            self.wizard.enable_finish()
        elif (pm_iface is IGiftCertificatePM
              or pm_iface is IMultiplePM):
            self.wizard.disable_finish()
        else:
            raise ValueError(
                "Invalid payment method interface, got %s" % pm_iface)


    #
    # AbstractSalesPersonStep hooks
    #

    def update_discount_and_surcharge(self):
        # Here we need avoid to reset sale data defined when creating the
        # Sale in the POS application, i.e, we should not reset the
        # discount and surcharge if they are already set (this is the
        # case when CONFIRM_SALES_ON_TILL parameter is enabled).
        if not sysparam(self.conn).CONFIRM_SALES_ON_TILL:
            self.model.reset_discount_and_surcharge()

    def setup_invoice_number_widgets(self):
        if not check_virtual_printer_for_current_station(self.conn):
            self.hide_invoice_number_widgets()
        self.force_validation()

    def on_payment_method_changed(self, slave, method_iface):
        self._update_next_step(method_iface)

    #
    # WizardStep hooks
    #

    def post_init(self):
        self.wizard.payment_group.clear_preview_payments()
        self.register_validate_function(self.wizard.refresh_next)
        self._update_next_step(self._get_selected_payment_method())
        self.force_validation()

    def on_next_step(self):
        selected_method = self._get_selected_payment_method()
        if selected_method is IMoneyPM:
            # Return None here means call wizard.finish, which is exactly
            # what we need
            self.wizard.setup_cash_payment()
            return

        elif selected_method is IGiftCertificatePM:
            table = GiftCertificate.getAdapterClass(ISellable)
            if not table.get_sold_sellables(self.conn):
                msg = _('There is no sold gift certificates at this moment.'
                        '\nPlease select another payment method.')
                warning(msg)
                return self
            step_class = GiftCertificateSelectionStep
        else:
            step_class = PaymentMethodStep
        return step_class(self.wizard, self, self.conn, self.model)


class PreOrderSalesPersonStep(AbstractSalesPersonStep):
    """A wizard step used when creating a pre order """

    #
    # AbstractSalesPersonStep hooks
    #

    def setup_invoice_number_widgets(self):
        self.hide_invoice_number_widgets()

    #
    # WizardStep hooks
    #

    def post_init(self):
        self.register_validate_function(self.wizard.refresh_next)
        self.wizard.enable_finish()
        self.force_validation()

    def on_next_step(self):
        # Return None here means call wizard.finish, which is exactly
        # what we need
        return


#
# Main wizard
#


class ConfirmSaleWizard(AbstractSaleWizard):
    """A wizard used when confirming a sale order. It means generate
    payments, fiscal data and update stock
    """
    first_step = SalesPersonStep
    title = _("Sale Checkout")

    @argcheck(object, GiftCertificateOverpaidSettings)
    def set_gift_certificate_settings(self, slave, settings):
        self.gift_certificate_settings = settings

    #
    # Hooks
    #

    def initialize(self):
        self.gift_certificates = []
        # Stores specific informations for orders with gift certificate
        self.gift_certificate_settings = None

    #
    # BaseWizard hooks
    #

    def finish(self):
        if self.gift_certificates:
            group = self.payment_group
            for certificate in self.gift_certificates:
                # FIXME: This is wrong, we must use IPaymentGroup's add_payment
                certificate.group = group
        self.model.confirm_sale(self.gift_certificate_settings)
        print_cheques_for_payment_group(self.conn,
                                        self.payment_group)
        self.retval = True
        self.close()


class PreOrderWizard(AbstractSaleWizard):
    """A wizard used to create a preorder which will be confirmed later. A
    pre order doesn't create payments, fiscal data and also doesn't update
    the stock for products
    """
    first_step = PreOrderSalesPersonStep
    title = _("Confirm PreOrder")

    #
    # BaseWizard hooks
    #

    def finish(self):
        self.model.validate()
        self.retval = True
        self.close()
