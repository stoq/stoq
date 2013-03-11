# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013 Async Open Source <http://www.async.com.br>
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

import datetime
import decimal

from kiwi.currency import currency
from kiwi.datatypes import ValidationError
from kiwi.ui.forms import PriceField, NumericField
from kiwi.ui.objectlist import Column
from storm.expr import And, Or

from stoqlib.api import api
from stoqlib.domain.person import LoginUser
from stoqlib.domain.product import ProductStockItem
from stoqlib.domain.sellable import Sellable
from stoqlib.domain.views import SellableFullStockView
from stoqlib.domain.workorder import WorkOrder, WorkOrderItem
from stoqlib.gui.editors.baseeditor import BaseEditorSlave, BaseEditor
from stoqlib.gui.wizards.abstractwizard import SellableItemSlave
from stoqlib.lib.formatters import format_quantity
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class _WorkOrderItemEditor(BaseEditor):
    model_name = _(u'Work order item')
    model_type = WorkOrderItem
    confirm_widgets = ['price', 'quantity']

    fields = dict(
        price=PriceField(_(u'Price'), proxy=True, mandatory=True),
        quantity=NumericField(_(u'Quantity'), proxy=True, mandatory=True),
        )

    def on_price__validate(self, widget, value):
        if value <= 0:
            return ValidationError(_(u"The price must be greater than 0"))

        sellable = self.model.sellable
        # FIXME: Because of the design of the editor, the client
        # could not be set yet.
        category = self.model.order.client and self.model.order.client.category
        if not sellable.is_valid_price(value, category):
            return ValidationError(_(u"Max discount for this product "
                                     u"is %.2f%%") % sellable.max_discount)

    def on_quantity__validate(self, entry, value):
        sellable = self.model.sellable
        storable = sellable.product_storable
        if not storable:
            return

        if value <= 0:
            return ValidationError(_(u"The quantity must be greater than 0"))

        if value > storable.get_balance_for_branch(self.model.order.branch):
            return ValidationError(_(u"This quantity is not available in stock"))

        if not sellable.is_valid_quantity(value):
            return ValidationError(_(u"This product unit (%s) does not "
                                     u"support fractions.") %
                                     sellable.get_unit_description())


class _WorkOrderItemSlave(SellableItemSlave):
    model_type = WorkOrder
    summary_label_text = '<b>%s</b>' % api.escape(_("Total:"))
    sellable_view = SellableFullStockView
    item_editor = _WorkOrderItemEditor
    validate_stock = True
    validate_value = True
    value_column = 'price'

    def __init__(self, store, model=None, visual_mode=False):
        super(_WorkOrderItemSlave, self).__init__(store, model=model,
                                                  visual_mode=visual_mode)
        self.hide_add_button()
        self.hide_del_button()

    #
    #  SellableItemSlave
    #

    def on_confirm(self):
        self.model.sync_stock()

    def get_columns(self, editable=True):
        return [
            Column('sellable.code', title=_(u'Code'),
                   data_type=str, visible=False),
            Column('sellable.barcode', title=_(u'Barcode'),
                   data_type=str, visible=False),
            Column('sellable.description', title=_(u'Description'),
                   data_type=str, expand=True),
            Column('price', title=_(u'Price'),
                   data_type=currency),
            Column('quantity', title=_(u'Quantity'),
                   data_type=decimal.Decimal, format_func=format_quantity),
            Column('total', title=_(u'Total'),
                   data_type=currency),
            ]

    def get_saved_items(self):
        return self.model.order_items

    def get_order_item(self, sellable, price, quantity):
        return self.model.add_sellable(sellable,
                                       price=price, quantity=quantity)

    def get_sellable_view_query(self):
        return (self.sellable_view,
                # FIXME: How to do this using sellable_view.find_by_branch ?
                And(Or(ProductStockItem.branch_id == self.model.branch.id,
                       ProductStockItem.branch_id == None),
                    Sellable.get_available_sellables_query(self.store)))


class WorkOrderOpeningSlave(BaseEditorSlave):
    gladefile = 'WorkOrderOpeningSlave'
    model_type = WorkOrder
    proxy_widgets = [
        'defect_reported',
        'open_date',
        ]

    #
    #  BaseEditorSlave
    #

    def setup_proxies(self):
        self.add_proxy(self.model, self.proxy_widgets)

        if not api.sysparam(self.store).ALLOW_OUTDATED_OPERATIONS:
            self.open_date.set_sensitive(False)


class WorkOrderQuoteSlave(BaseEditorSlave):
    gladefile = 'WorkOrderQuoteSlave'
    model_type = WorkOrder
    proxy_widgets = [
        'defect_detected',
        'quote_responsible',
        'estimated_cost',
        'estimated_finish',
        'estimated_hours',
        'estimated_start',
        ]

    #
    #  BaseEditorSlave
    #

    def setup_proxies(self):
        self._fill_quote_responsible_combo()

        self.add_proxy(self.model, self.proxy_widgets)

    #
    #  Private
    #

    def _fill_quote_responsible_combo(self):
        users = LoginUser.get_active_users(self.store)
        self.quote_responsible.prefill(api.for_person_combo(users))

    #
    #  Callbacks
    #

    def on_estimated_start__validate(self, widget, value):
        sysparam_ = api.sysparam(self.store)
        if (value < datetime.date.today() and
                not sysparam_.ALLOW_OUTDATED_OPERATIONS):
            return ValidationError(u"The start date cannot be on the past")

        self.estimated_finish.validate(force=True)

    def on_estimated_finish__validate(self, widget, value):
        estimated_start = self.estimated_start.read()
        if value and not estimated_start:
            return ValidationError(
                _(u"To define a finish date you must define a start date too"))

        if value < estimated_start:
            return ValidationError(
                _(u"Finished date needs to be after start date"))


class WorkOrderExecutionSlave(BaseEditorSlave):
    gladefile = 'WorkOrderExecutionSlave'
    model_type = WorkOrder
    proxy_widgets = [
        'execution_responsible',
        ]

    #
    #  BaseEditorSlave
    #

    def setup_proxies(self):
        self._fill_execution_responsible_combo()

        self.proxy = self.add_proxy(self.model, self.proxy_widgets)

    def setup_slaves(self):
        self.sellable_item_slave = _WorkOrderItemSlave(
            self.store, self.model, visual_mode=self.visual_mode)
        self.attach_slave('sellable_item_holder', self.sellable_item_slave)

    #
    #  Private
    #

    def _fill_execution_responsible_combo(self):
        users = LoginUser.get_active_users(self.store)
        self.execution_responsible.prefill(api.for_person_combo(users))
