# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4
##
## Copyright (C) 2011 Async Open Source <http://www.async.com.br>
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
""" Dialog to set the price for sellables"""

from decimal import Decimal
from sys import maxint as MAXINT

import gtk

from kiwi import ValueUnset
from kiwi.datatypes import currency
from kiwi.enums import ListType
from kiwi.ui.objectlist import Column
from kiwi.ui.listdialog import ListSlave

from stoqlib.database.runtime import (new_transaction, finish_transaction,
                                      get_current_branch)
from stoqlib.domain.sellable import Sellable, ClientCategoryPrice
from stoqlib.domain.views import SellableFullStockView
from stoqlib.domain.person import ClientCategory
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.lib.message import yesno
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class _TemporarySellableItem(object):
    def __init__(self, sellable_view, categories):
        self.sellable_view = sellable_view
        self.sellable = sellable_view.sellable
        self.code = sellable_view.code
        self.barcode = sellable_view.barcode
        self.category_description = sellable_view.category_description
        self.description = sellable_view.description
        self.cost = sellable_view.cost
        self.price = sellable_view.price
        self.max_discount = sellable_view.max_discount

        self._new_prices = {}
        for info in self.sellable.get_category_prices():
            self.set_price(info.category, info.price)

    def set_markup(self, category, markup):
        price = self.cost + self.cost * markup / 100
        if price <= 0:
            price = Decimal('0.01')
        self.set_price(category, currency(price))

    def set_price(self, category, price):
        self._new_prices[category] = price
        if category:
            setattr(self, 'price_%s' % category.id, price)
        else:
            self.price = price

    def save_changes(self):
        for cat, value in self._new_prices.items():
            info = self.sellable.get_category_price_info(cat)
            if not info:
                info = ClientCategoryPrice(sellable=self.sellable,
                                           category=cat,
                                           max_discount=self.max_discount,
                                           price=value,
                                           connection=self.sellable.get_connection())
            else:
                info.price = value
            print 'updating', cat, value


class SellablePriceDialog(BaseEditor):
    gladefile = "SellablePriceDialog"
    model_type = object
    title = _(u"Price Change Dialog")
    size = (750, 450)

    def __init__(self, conn):
        self.categories = ClientCategory.select(connection=conn)
        self._last_cat = None

        BaseEditor.__init__(self, conn, model=object())
        self._setup_widgets()

    def _setup_widgets(self):
        cats = [(i.get_description(), i) for i in self.categories]
        cats.insert(0, ('Default Price', None))
        self.category.prefill(cats)
        self._sellables = [_TemporarySellableItem(s, self.categories)
            for s in SellableFullStockView.select(connection=self.conn)]
        self.slave.listcontainer.add_items(self._sellables)

    def _get_columns(self):
        self._price_columns = {}
        columns = [Column("code", title=_(u"Code"), data_type=str,
                       sorted=True, width=100),
                Column("barcode", title=_(u"Barcode"), data_type=str,
                       width=100),
                Column("category_description", title=_(u"Category"),
                       data_type=str, width=100),
                Column("description", title=_(u"Description"),
                       data_type=str, expand=True),
                Column("cost", title=_(u"Cost"),
                       data_type=currency, width=90),
                Column("price", title=_(u"Default Price"),
                       data_type=currency, width=90)
                       ]

        self._price_columns[None] = columns[-1]
        for cat in self.categories:
            columns.append(Column('price_%s' % (cat.id,),
                               title=cat.get_description(), data_type=currency,
                               width=90, visible=False))
            self._price_columns[cat.id] = columns[-1]
        self._columns = columns
        return columns

    def _format_qty(self, quantity):
        if quantity is ValueUnset:
            return None
        if quantity >= 0:
            return quantity

    def _validate_initial_stock_quantity(self, item, trans):
        positive = item.initial_stock > 0
        if item.initial_stock is not ValueUnset and positive:
            storable = trans.get(item.obj)
            #storable.increase_stock(item.initial_stock, self._branch)

    #
    # BaseEditorSlave
    #

    def setup_slaves(self):
        self.slave = ListSlave(self._get_columns())
        self.slave.set_list_type(ListType.READONLY)
        self.attach_slave("on_slave_holder" , self.slave)

    def on_confirm(self):
        for i in self._sellables:
            i.save_changes()
        return True

    #
    #   Callbacks
    #

    def on_apply__clicked(self, button):
        markup = self.markup.read()
        cat = self.category.read()
        for i in self._sellables:
            i.set_markup(cat, markup)
            self.slave.listcontainer.list.refresh(i)

    def on_category__changed(self, widget):
        cat = self.category.read()
        self._price_columns[self._last_cat].visible = False
        if cat:
            self._price_columns[cat.id].visible = True
            self._last_cat = cat.id
        else:
            self._price_columns[None].visible = True
            self._last_cat = None
        self.slave.listcontainer.list.set_columns(self._columns)
