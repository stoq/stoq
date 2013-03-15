# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2008 Async Open Source <http://www.async.com.br>
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
""" Dialogs for quotes """

from decimal import Decimal

from kiwi.currency import currency
from kiwi.enums import ListType
from kiwi.python import AttributeForwarder
from kiwi.ui.objectlist import Column
from kiwi.ui.listdialog import ListSlave
from storm.expr import And, LeftJoin, Or

from stoqlib.domain.purchase import PurchaseOrder, PurchaseItem
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.lib.formatters import get_formatted_cost
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class _TemporaryQuoteItem(AttributeForwarder):
    attributes = ['quantity', 'cost']

    def __init__(self, item):
        AttributeForwarder.__init__(self, item)

        self.description = item.sellable.get_description()
        self.quantity = item.quantity
        self.cost = item.cost
        self.last_cost = self._get_last_cost(item)
        self.average_cost = self._get_average_cost(item)

    def _get_purchase_items_by_sellable(self):
        query = And(PurchaseItem.sellable_id == self.target.sellable.id,
                    Or(PurchaseOrder.status == PurchaseOrder.ORDER_CONFIRMED,
                       PurchaseOrder.status == PurchaseOrder.ORDER_CLOSED))
        join = LeftJoin(PurchaseOrder,
                        PurchaseItem.order_id == PurchaseOrder.id)
        store = self.target.store
        return store.using(PurchaseItem, join).find(PurchaseItem, query)

    def _get_last_cost(self, item):
        purchase_items = list(self._get_purchase_items_by_sellable())
        if purchase_items:
            return currency(purchase_items[-1].cost)
        return currency(item.cost)

    def _get_average_cost(self, item):
        cost = self._get_purchase_items_by_sellable().avg(PurchaseItem.cost)
        if cost:
            return currency(cost)
        return currency(item.cost)


class QuoteFillingDialog(BaseEditor):
    gladefile = "HolderTemplate"
    model_type = PurchaseOrder
    title = _(u"Quote Filling")
    size = (750, 450)

    def __init__(self, model, store):
        BaseEditor.__init__(self, store, model)
        self._setup_widgets()

    def _setup_widgets(self):
        self.slave.listcontainer.add_items(self._get_quote_items())

    def _get_columns(self):
        return [Column("description", title=_(u"Description"), sorted=True,
                       data_type=str, expand=True),
                Column("quantity", title=_(u"Quantity"), data_type=Decimal,
                       editable=True),
                Column("cost", title=_(u"Cost"), data_type=currency,
                       format_func=get_formatted_cost, editable=True),
                Column("last_cost", title=_(u"Last Cost"), data_type=currency,
                       format_func=get_formatted_cost),
                Column("average_cost", title=_(u"Average Cost"),
                       data_type=currency, format_func=get_formatted_cost),
                ]

    def _get_quote_items(self):
        return [_TemporaryQuoteItem(item)
                for item in self.model.get_items()]

    #
    # BaseEditorSlave
    #

    def setup_slaves(self):
        self.slave = ListSlave(self._get_columns())
        self.slave.set_list_type(ListType.READONLY)
        self.attach_slave("place_holder", self.slave)
