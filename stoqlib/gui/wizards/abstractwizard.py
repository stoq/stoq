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
""" Abstract wizard and wizard steps definition

Note that a good aproach for all wizards steps defined here is do
not require some specific implementation details for the main wizard. Use
instead signals and interfaces for that.
"""

from decimal import Decimal

from kiwi.ui.widgets.list import SummaryLabel
from kiwi.datatypes import currency
from kiwi.python import Settable
from kiwi.argcheck import argcheck

from stoqlib.database.runtime import StoqlibTransaction
from stoqlib.exceptions import StoqlibError, BarcodeDoesNotExists
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.defaults import get_all_methods_dict
from stoqlib.gui.base.wizards import WizardEditorStep, BaseWizard
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.base.lists import AdditionListSlave
from stoqlib.gui.editors.noteeditor import NoteEditor
from stoqlib.gui.slaves.paymentmethodslave import SelectPaymentMethodSlave
from stoqlib.gui.slaves.saleslave import DiscountSurchargeSlave
from stoqlib.domain.sale import Sale
from stoqlib.domain.payment.payment import AbstractPaymentGroup
from stoqlib.domain.person import Person
from stoqlib.domain.interfaces import IPaymentGroup, ISalesPerson
from stoqlib.domain.sellable import ASellable
from stoqlib.domain.giftcertificate import GiftCertificate

_ = stoqlib_gettext

#
# Abstract Wizards for sales
#

class AbstractSaleWizard(BaseWizard):
    """An abstract wizard for sale orders"""
    size = (600, 400)
    first_step = None
    title = None

    def __init__(self, conn, model):
        self._check_payment_group(model, conn)
        self.initialize()
        # Saves the initial state of the sale order and allow us to call
        # rollback safely when it's needed
        conn.commit()
        first_step = self.first_step(self, conn, model, self.payment_group)
        BaseWizard.__init__(self, conn, first_step, model)

    def _check_payment_group(self, model, conn):
        if not isinstance(model, Sale):
            raise StoqlibError("Invalid datatype for model, it should be "
                               "of type Sale, got %s instead" % model)
        group = IPaymentGroup(model, None)
        if not group:
            group = model.addFacet(IPaymentGroup, connection=conn)
        self.payment_group = group

    #
    # Hooks
    #

    def initialize(self):
        """Overwrite this method on child when performing some tasks before
        calling the wizard constructor is an important requirement
        """

    #
    # Public API
    #

    def setup_cash_payment(self, total=None):
        money_method = sysparam(self.conn).METHOD_MONEY
        total = total or self.payment_group.get_total_received()
        money_method.setup_inpayments(total, self.payment_group)

    #
    # BaseWizard hooks
    #

    def finish(self):
        raise NotImplementedError("This method must be overwritten on child")



class AbstractSalesPersonStep(WizardEditorStep):
    """ An abstract step which allows to define a salesperson, the sale's
    discount and surcharge, when it is needed.
    """
    gladefile = 'SalesPersonStep'
    model_type = Sale
    proxy_widgets = ('total_lbl',
                     'subtotal_lbl',
                     'salesperson_combo')

    @argcheck(BaseWizard, StoqlibTransaction, Sale, AbstractPaymentGroup)
    def __init__(self, wizard, conn, model, payment_group):
        self.payment_group = payment_group
        WizardEditorStep.__init__(self, conn, wizard, model)
        self.update_discount_and_surcharge()

    def _update_totals(self):
        for field_name in ('total_sale_amount', 'sale_subtotal'):
            self.proxy.update(field_name)

    def setup_widgets(self):
        salespersons = Person.iselect(ISalesPerson, connection=self.conn)
        items = [(s.get_adapted().name, s) for s in salespersons]
        self.salesperson_combo.prefill(items)
        if not sysparam(self.conn).ACCEPT_CHANGE_SALESPERSON:
            self.salesperson_combo.set_sensitive(False)
        else:
            self.salesperson_combo.grab_focus()

    def _get_selected_payment_method(self):
        return self.pm_slave.get_selected_method()

    #
    # Hooks
    #

    def update_discount_and_surcharge(self):
        """Update discount and surcharge values when it's needed"""

    def on_payment_method_changed(self, slave, method_iface):
        """Overwrite this method when controling the status of finish button
        is a required task when changing payment methods
        """

    def on_next_step(self):
        raise NotImplementedError("Overwrite on child to return the "
                                  "proper next step or None for finish")

    #
    # WizardStep hooks
    #

    def next_step(self):
        self.payment_group.set_method(self.pm_slave.get_selected_method())
        return self.on_next_step()

    #
    # BaseEditorSlave hooks
    #

    def setup_slaves(self):
        self.discsurcharge_slave = DiscountSurchargeSlave(self.conn, self.model,
                                                          self.model_type)
        self.discsurcharge_slave.connect('discount-changed',
                                         self.on_discsurcharge_slave_changed)
        slave_holder = 'discount_surcharge_slave'
        if self.get_slave(slave_holder):
            self.detach_slave(slave_holder)
        self.attach_slave('discount_surcharge_slave', self.discsurcharge_slave)

        group = IPaymentGroup(self.model, None)
        if not group:
            raise StoqlibError(
                "You should have a IPaymentGroup facet defined at this point")
        self.pm_slave = SelectPaymentMethodSlave(
            method_iface=get_all_methods_dict()[group.default_method])
        self.pm_slave.connect('method-changed', self.on_payment_method_changed)
        self.attach_slave('select_method_holder', self.pm_slave)

    def setup_proxies(self):
        self.setup_widgets()
        self.proxy = self.add_proxy(self.model,
                                    AbstractSalesPersonStep.proxy_widgets)

    #
    # Callbacks
    #

    def on_discsurcharge_slave_changed(self, slave):
        self._update_totals()

    def on_notes_button__clicked(self, *args):
        run_dialog(NoteEditor, self, self.conn, self.model, 'notes',
                   title=_("Additional Information"))


#
# Abstract Wizards for items
#


class SellableItemStep(WizardEditorStep):
    """An abstract item step for purchases and receiving orders."""
    gladefile = 'AbstractItemStep'
    item_widgets = ('item',)
    proxy_widgets = ('quantity',
                     'unit_label',
                     'cost')
    model_type = None
    table = ASellable
    item_table = None
    summary_label_text = None
    list_slave_class = AdditionListSlave

    def __init__(self, wizard, previous, conn, model):
        WizardEditorStep.__init__(self, conn, wizard, model, previous)
        self._update_widgets()
        self.unit_label.set_bold(True)

    def _refresh_next(self):
        self.wizard.refresh_next(len(self.slave.klist))

    def setup_item_entry(self):
        result = ASellable.get_unblocked_sellables(self.conn)
        self.item.prefill([(item.get_description(), item)
                               for item in result
                                   if not isinstance(item.get_adapted(),
                                                     GiftCertificate)])

    def get_columns(self):
        raise NotImplementedError('This method must be defined on child')

    def _update_widgets(self):
        has_item_str = self.item.get_text() != ''
        self.add_item_button.set_sensitive(has_item_str)

    def _get_sellable(self):
        if self.proxy.model:
            sellable = self.item_proxy.model.item
        else:
            sellable = None
        if not sellable:
            barcode = self.item.get_text()
            try:
                sellable = ASellable.get_availables_and_sold_by_barcode(
                    self.conn, barcode)
            except BarcodeDoesNotExists, e:
                self.item.set_invalid(str(e))
                sellable = None

            if sellable:
                # Waiting for a select method on kiwi entry using entry
                # completions
                self.item.set_text(sellable.get_short_description())
        self.add_item_button.set_sensitive(sellable is not None)
        return sellable

    def _update_total(self, *args):
        self.summary.update_total()
        self._refresh_next()
        self.force_validation()

    def _update_list(self, item):
        if self.item_proxy.model.item is item:
            cost = self.proxy.model.cost
        else:
            cost = item.cost
        quantity = (self.proxy.model and self.proxy.model.quantity or
                    Decimal(1))

        # For items already present in the list, increase the quantity of the
        # existing item. If the item is not in the list, just add it.
        items = [s.sellable for s in self.slave.klist]
        if item in items:
            object_item = self.slave.klist[items.index(item)]
            object_item.quantity += quantity
            self.slave.klist.update(object_item)
        else:
            order_item = self.get_order_item(item, cost, quantity)
            self.slave.klist.append(order_item)
        self._update_total()
        self.proxy.set_model(None, relax_type=True)
        self.item.set_text('')
        self.item.grab_focus()

    def get_order_item(self):
        raise NotImplementedError('This method must be defined on child')

    def _add_item(self):
        if not self.add_item_button.get_property('sensitive'):
            return
        self.add_item_button.set_sensitive(False)
        item = self._get_sellable()
        if not item:
            return
        self._update_list(item)

    def get_saved_items(self):
        raise NotImplementedError('This method must be defined on child')

    #
    # WizardStep hooks
    #

    def next_step(self):
        raise NotImplementedError('This method must be defined on child')

    def post_init(self):
        self.item.grab_focus()
        self.item_hbox.set_focus_chain([self.item,
                                        self.quantity, self.cost,
                                        self.add_item_button,
                                        self.product_button])
        self.register_validate_function(self.wizard.refresh_next)
        self.force_validation()

    def setup_proxies(self):
        self.setup_item_entry()
        self.proxy = self.add_proxy(None, SellableItemStep.proxy_widgets)
        model = Settable(quantity=Decimal(1), price=currency(0),
                         item=None)
        self.item_proxy = self.add_proxy(model,
                                         SellableItemStep.item_widgets)

    def setup_slaves(self):
        items = self.get_saved_items()
        self.slave = self.list_slave_class(self.conn, self.get_columns(),
                                           klist_objects=items)
        self.slave.connect('before-delete-items', self._before_delete_items)
        self.slave.connect('after-delete-items', self._update_total)
        self.slave.connect('on-edit-item', self._update_total)
        value_format = '<b>%s</b>'
        self.summary = SummaryLabel(klist=self.slave.klist, column='total',
                                    label=self.summary_label_text,
                                    value_format=value_format)
        self.summary.show()
        self.slave.list_vbox.pack_start(self.summary, expand=False)
        self.attach_slave('list_holder', self.slave)

    #
    # callbacks
    #

    def _before_delete_items(self, slave, items):
        for item in items:
            self.item_table.delete(item.id, connection=self.conn)
        self._refresh_next()

    def on_product_button__clicked(self, *args):
        raise NotImplementedError('This method must be defined on child')

    def on_add_item_button__clicked(self, *args):
        self._add_item()

    def on_item__activate(self, *args):
        self._get_sellable()
        self.quantity.grab_focus()

    def after_item__content_changed(self, *args):
        self.item.set_valid()
        self._update_widgets()
        item = self.item_proxy.model.item
        if not (item and self.item.get_text()):
            self.proxy.set_model(None, relax_type=True)
            return
        cost = item.cost
        model = Settable(quantity=Decimal(1), cost=cost,
                         item=item)
        self.proxy.set_model(model)

    def on_quantity__activate(self, *args):
        self._add_item()

    def on_cost__activate(self, *args):
        self._add_item()
