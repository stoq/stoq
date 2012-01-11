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

import gtk

from kiwi.datatypes import currency
from kiwi.enums import ListType
from kiwi.ui.objectlist import Column
from kiwi.ui.listdialog import ListSlave

from stoqlib.database.orm import LEFTJOINOn
from stoqlib.domain.sellable import (Sellable, ClientCategoryPrice,
                                     SellableCategory)
from stoqlib.domain.person import ClientCategory
from stoqlib.gui.dialogs.progressdialog import ProgressDialog
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.lib.message import marker
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext

from stoqlib.database.orm import Viewable


class CategoryPriceView(Viewable):
    columns = dict(
        id=ClientCategoryPrice.q.id,
        sellable_id=ClientCategoryPrice.q.sellableID,
        category_id=ClientCategoryPrice.q.categoryID,
        price=ClientCategoryPrice.q.price,
        max_discount=ClientCategoryPrice.q.max_discount,
    )

    joins = []


class SellableView(Viewable):
    columns = dict(
        id=Sellable.q.id,
        code=Sellable.q.code,
        barcode=Sellable.q.barcode,
        status=Sellable.q.status,
        cost=Sellable.q.cost,
        category_description=SellableCategory.q.description,
        description=Sellable.q.description,
        price=Sellable.q.base_price,
        max_discount=Sellable.q.max_discount,
    )

    joins = [
        # Category
        LEFTJOINOn(None, SellableCategory,
                   SellableCategory.q.id == Sellable.q.categoryID),
    ]

    def __init__(self, *args, **kargs):
        self._new_prices = {}
        Viewable.__init__(self, *args, **kargs)

    def set_markup(self, category, markup):
        price = self.cost + self.cost * markup / 100
        if price <= 0:
            price = Decimal('0.01')
        self.set_price(category.id, currency(price))

    def set_price(self, category_id, price):
        self._new_prices[category_id] = price
        setattr(self, 'price_%s' % category_id, price)

    def save_changes(self):
        for cat, value in self._new_prices.items():
            info = ClientCategoryPrice.selectOneBy(sellableID=self.id,
                                                category=cat,
                                                connection=self.get_connection())
            if not info:
                info = ClientCategoryPrice(sellableID=self.id,
                                           category=cat,
                                           max_discount=self.max_discount,
                                           price=value,
                                           connection=self.get_connection())
            else:
                info.price = value


class SellablePriceDialog(BaseEditor):
    gladefile = "SellablePriceDialog"
    model_type = object
    title = _(u"Price Change Dialog")
    size = (850, 450)

    def __init__(self, conn):
        self.categories = ClientCategory.select(connection=conn)
        self._last_cat = None

        BaseEditor.__init__(self, conn, model=object())
        self._setup_widgets()

    def _setup_widgets(self):
        cats = [(i.get_description(), i) for i in self.categories]
        self.category.prefill(cats)

        prices = CategoryPriceView.select(connection=self.conn)
        category_prices = {}
        for p in prices:
            c = category_prices.setdefault(p.sellable_id, {})
            c[p.category_id] = p.price

        marker('SellableView')
        sellables = SellableView.select(connection=self.conn)
        self._sellables = sellables

        marker('add_items')
        for s in sellables:
            for category_id, price in category_prices.get(s.id, {}).items():
                s.set_price(category_id, price)
            self.slave.listcontainer.list.append(s)
        marker('Done add_items')

    def _get_columns(self):
        marker('_get_columns')
        self._price_columns = {}
        columns = [Column("code", title=_(u"Code"), data_type=str,
                       width=100),
                Column("barcode", title=_(u"Barcode"), data_type=str,
                       width=100, visible=False),
                Column("category_description", title=_(u"Category"),
                       data_type=str, width=100),
                Column("description", title=_(u"Description"),
                       data_type=str, width=200),
                Column("cost", title=_(u"Cost"),
                       data_type=currency, width=90),
                Column("price", title=_(u"Default Price"),
                       data_type=currency, width=90)
                       ]

        self._price_columns[None] = columns[-1]
        for cat in self.categories:
            columns.append(Column('price_%s' % (cat.id, ),
                               title=cat.get_description(), data_type=currency,
                               width=90, visible=True))
            self._price_columns[cat.id] = columns[-1]
        self._columns = columns
        marker('Done _get_columns')
        return columns

    #
    # BaseEditorSlave
    #

    def setup_slaves(self):
        self.slave = ListSlave(self._get_columns())
        self.slave.set_list_type(ListType.READONLY)
        self.attach_slave("on_slave_holder", self.slave)

    def on_cancel(self):
        # Call clear on objectlist before destruction. Workaround for a bug
        # when destructing the dialog taking to long
        self.slave.listcontainer.list.clear()
        return False

    def on_confirm(self):
        marker('Saving prices')
        # FIXME: Improve this part. This is just a quick workaround to
        # release the bugfix asap
        self.main_dialog.ok_button.set_sensitive(False)
        self.main_dialog.cancel_button.set_sensitive(False)
        d = ProgressDialog(_('Updating items'), pulse=False)
        d.set_transient_for(self.main_dialog)
        d.start(wait=0)
        d.cancel.hide()

        total = len(self.slave.listcontainer.list)
        for i, s in enumerate(self.slave.listcontainer.list):
            s.save_changes()
            d.progressbar.set_text('%s/%s' % (i + 1, total))
            d.progressbar.set_fraction((i + 1) / float(total))
            while gtk.events_pending():
                gtk.main_iteration(False)

        d.stop()
        marker('Done saving prices')
        self.slave.listcontainer.list.clear()
        return True

    #
    #   Callbacks
    #

    def on_apply__clicked(self, button):
        markup = self.markup.read()
        cat = self.category.read()
        marker('Updating prices')
        for i in self.slave.listcontainer.list:
            i.set_markup(cat, markup)
            self.slave.listcontainer.list.refresh(i)
        marker('Done updating prices')
