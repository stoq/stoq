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

import gtk

from kiwi.datatypes import currency
from kiwi.enums import ListType
from kiwi.python import AttributeForwarder
from kiwi.ui.objectlist import Column
from kiwi.ui.listdialog import ListSlave

from stoqlib.api import api
from stoqlib.database.orm import AND, OR, LEFTJOINOn
from stoqlib.domain.interfaces import IEmployee
from stoqlib.domain.production import ProductionOrder, ProductionMaterial
from stoqlib.domain.purchase import PurchaseOrder, PurchaseItem
from stoqlib.domain.sale import Sale
from stoqlib.gui.base.lists import SimpleListDialog
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.lib.formatters import get_formatted_cost
from stoqlib.lib.message import info
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
        query = AND(PurchaseItem.q.sellableID == self.target.sellable.id,
                    OR(PurchaseOrder.q.status == PurchaseOrder.ORDER_CONFIRMED,
                       PurchaseOrder.q.status == PurchaseOrder.ORDER_CLOSED))
        join = LEFTJOINOn(None, PurchaseOrder,
                          PurchaseItem.q.orderID == PurchaseOrder.q.id)
        conn = self.target.get_connection()
        return PurchaseItem.select(query, join=join, connection=conn)

    def _get_last_cost(self, item):
        purchase_items = list(self._get_purchase_items_by_sellable())
        if purchase_items:
            return currency(purchase_items[-1].cost)
        return currency(item.cost)

    def _get_average_cost(self, item):
        cost = self._get_purchase_items_by_sellable().avg('cost')
        if cost:
            return currency(cost)
        return currency(item.cost)


class QuoteFillingDialog(BaseEditor):
    gladefile = "HolderTemplate"
    model_type = PurchaseOrder
    title = _(u"Quote Filling")
    size = (750, 450)

    def __init__(self, model, conn):
        BaseEditor.__init__(self, conn, model)
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

    def on_confirm(self):
        return True


class ConfirmSaleMissingDialog(SimpleListDialog):
    """This dialog shows a list of missing products to confirm a Sale

    Unless the user cancel the dialog, the Sale will change the status from
    QUOTE to ORDERED.

    Also, for all productis missing that are composed, a new production order
    will be created.
    """

    def __init__(self, sale, missing_items):
        self.sale = sale
        self.missing = missing_items
        msg = '<b>%s</b>' % _("The following items don't have enough stock to "
                              "confirm the sale")
        SimpleListDialog.__init__(self, self._get_columns(), missing_items,
                                  hide_cancel_btn=False,
                                  title=_('Missing items'))
        self.header_label.set_markup(msg)
        self.header_label.show()

        if sale.status == Sale.STATUS_QUOTE:
            label = gtk.Label(_('Do you want to order the sale instead?'))
            self.notice.add(label)
            label.show()
            self.set_ok_label(_('Order sale'))

    def _get_columns(self):
        return [Column('description', title=_(u'Product'),
                        data_type=str, expand=True),
                Column('ordered', title=_(u'Ordered'),
                       data_type=int),
                Column('stock', title=_(u'Stock'),
                       data_type=int)]

    def _create_production_order(self, trans):
        desc = _('Production for Sale order %s') % self.sale.get_order_number_str()
        if self.sale.client:
            desc += ' (%s)' % self.sale.client.get_name()
        user = api.get_current_user(trans)
        employee = IEmployee(user.person, None)
        order = ProductionOrder(branch=self.sale.branch,
                    status=ProductionOrder.ORDER_WAITING,
                    responsible=employee,
                    description=desc,
                    connection=trans)

        materials = {}
        for item in self.missing:
            product = item.storable.product
            components = list(product.get_components())
            if not components:
                continue
            qty = item.ordered - item.stock
            order.add_item(product.sellable, qty)

            # Merge possible duplicate components from different products
            for component in components:
                materials.setdefault(component.component, 0)
                materials[component.component] += component.quantity * qty

        for material, needed in materials.items():
            ProductionMaterial(needed=needed,
                               order=order,
                               product=material,
                               connection=trans)

        if materials:
            info(_('A new production was created for the missing composed '
                   'products'))
        else:
            ProductionOrder.delete(order.id, trans)

    def confirm(self, *args):
        if self.sale.status == Sale.STATUS_QUOTE:
            trans = api.new_transaction()
            sale = trans.get(self.sale)
            self._create_production_order(trans)
            sale.order()
            api.finish_transaction(trans, True)
            trans.close()
        return SimpleListDialog.confirm(self, *args)
