# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2013 Async Open Source <http://www.async.com.br>
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

import gtk

from kiwi.python import Settable
from kiwi.ui.objectlist import Column

from stoqlib.api import api
from stoqlib.database.runtime import get_current_branch
from stoqlib.domain.production import ProductionMaterial, ProductionOrder
from stoqlib.domain.sale import Sale, SaleItem
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.base.lists import SimpleListDialog
from stoqlib.lib.message import info
from stoqlib.lib.translation import stoqlib_gettext as _


class MissingItemsDialog(SimpleListDialog):
    """This dialog shows a list of missing products to confirm a stock
    operation

    Unless the user cancel the dialog, if the operation is a Sale, it will
    change the status from QUOTE to ORDERED. Also, for all productis missing
    that are composed, a new production order will be created.

    If it's not a Sale, the dialog is just informative and does not change
    anything.
    """

    def __init__(self, order, missing):
        self.order = order
        self._is_sale_quote = (isinstance(order, Sale) and
                               order.status == Sale.STATUS_QUOTE)
        self.missing = missing
        msg = '<b>%s</b>' % (
            api.escape(_("The following items don't have enough stock to "
                         "confirm.")))
        SimpleListDialog.__init__(self, self._get_columns(), missing,
                                  hide_cancel_btn=not self._is_sale_quote,
                                  title=_('Missing items'),
                                  header_text=msg)

        if self._is_sale_quote:
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

    def _create_production_order(self, store):
        desc = _(u'Production for Sale order %s') % self.order.identifier
        if self.order.client:
            desc += ' (%s)' % self.order.client.get_name()
        user = api.get_current_user(store)
        employee = user.person.employee
        prod_order = ProductionOrder(branch=store.fetch(self.order.branch),
                                     status=ProductionOrder.ORDER_WAITING,
                                     responsible=employee,
                                     description=desc,
                                     store=store)

        materials = {}
        for item in self.missing:
            product = store.fetch(item.storable.product)
            components = list(product.get_components())
            if not components:
                continue
            qty = item.ordered - item.stock
            prod_order.add_item(product.sellable, qty)

            # Merge possible duplicate components from different products
            for component in components:
                materials.setdefault(component.component, 0)
                materials[component.component] += component.quantity * qty

        for material, needed in materials.items():
            ProductionMaterial(needed=needed,
                               order=prod_order,
                               product=material,
                               store=store)

        if materials:
            info(_('A new production was created for the missing composed '
                   'products'))
        else:
            store.remove(prod_order)

    def confirm(self, *args):
        if self._is_sale_quote:
            store = api.new_store()
            sale = store.fetch(self.order)
            self._create_production_order(store)
            sale.order()
            store.confirm(True)
            store.close()
        return SimpleListDialog.confirm(self, *args)


def get_missing_items(order, store):
    """
    Fetch missing items, the returning object has the following attributes set:

      - storable: A |storable| for the missing item;
      - description: A description for the missing item;
      - ordered: The quantity ordered of the missing item;
      - stock: The stock available of the missing item.

    :returns: a list of Settable items with the attributes mentioned above
    """
    # Lets confirm that we can create the sale, before opening the coupon
    prod_sold = {}
    prod_desc = {}
    for item in order.get_items():
        # Skip services, since we don't need stock to sell.
        if isinstance(item, SaleItem) and item.is_service():
            continue
        storable = item.sellable.product_storable
        # There are some products that we dont control the stock
        if not storable:
            continue
        prod_sold.setdefault(storable, 0)
        prod_sold[storable] += item.quantity
        if isinstance(item, SaleItem):
            prod_sold[storable] -= item.quantity_decreased
        prod_desc[storable] = item.sellable.get_description()

    branch = get_current_branch(store)
    missing = []
    for storable in prod_sold.keys():
        stock = storable.get_balance_for_branch(branch)
        if stock < prod_sold[storable]:
            missing.append(Settable(
                storable=storable,
                description=prod_desc[storable],
                ordered=prod_sold[storable],
                stock=stock))
    return missing


if __name__ == '__main__':  # pragma nocover
    ec = api.prepare_test()
    sale_ = ec.create_sale()
    sale_.status = Sale.STATUS_QUOTE
    missingitems = [Settable(description='foo',
                             ordered=False,
                             stock=True)]
    run_dialog(MissingItemsDialog, None, sale_, missingitems)
