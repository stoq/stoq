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
##

from decimal import Decimal

import gtk
from gtk import gdk

from kiwi.datatypes import currency
from kiwi.utils import gsignal
from kiwi.ui.delegates import GladeSlaveDelegate
from kiwi.ui.objectlist import Column, ColoredColumn

from stoqlib.api import api
from stoqlib.domain.interfaces import IStorable
from stoqlib.domain.product import Product
from stoqlib.domain.payment.group import PaymentGroup
from stoqlib.domain.purchase import PurchaseOrder, PurchaseItem
from stoqlib.domain.views import (ProductFullStockView,
                                  PurchasedItemAndStockView)
from stoqlib.exceptions import StockError
from stoqlib.gui.base.dialogs import BasicWrappingDialog, run_dialog
from stoqlib.gui.dialogs.csvexporterdialog import CSVExporterDialog
from stoqlib.gui.wizards.purchasewizard import PurchaseWizard
from stoqlib.lib.message import warning, yesno
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class _TemporaryProductionItem(object):
    def __init__(self, productview):
        self.product = productview.product
        self.code = productview.id
        self.cost = productview.cost
        self.description = productview.description
        self.category = productview.category_description
        self.unit = productview.get_unit_description()

        self.last_quantity = Decimal(0)
        self.quantity = Decimal(1)

    def __str__(self):
        return self.description

    def can_update_quantity(self):
        if self.quantity < 0:
            self.quantity = self.last_quantity
            return False
        return True

    def get_components(self):
        return self.product.get_components()


class _TemporaryProductionItemComponent(object):
    def __init__(self, product_component):
        self.product = product_component.component
        sellable = self.product.sellable
        self.code = sellable.code
        self.description = sellable.get_description()
        self.location = self.product.location
        if sellable.category:
            self.category = sellable.category.description
        else:
            self.category = ""

        self.industrialized = self.product.has_components()
        self.not_industrialized = not self.industrialized

        self.needed_quantity = product_component.quantity
        self.cost = sellable.cost
        self.total = sellable.cost
        self.last_quantity = Decimal(0)
        self.stock_quantity = self._get_stock_quantity()
        self.purchase_quantity = self._get_purchase_quantity()
        self.make_quantity = self._get_make_quantity()

        #XXX: workaround!
        conn = api.get_connection()
        items = PurchasedItemAndStockView.select(
            Product.q.id == self.product.id, connection=conn)
        self.to_receive = sum(
            [i.purchased - i.received for i in items], Decimal(0))

    def _get_stock_quantity(self):
        """Returns the quantity we have in stock of this component
        """
        storable = IStorable(self.product, None)
        if storable is None:
            return Decimal(0)

        try:
            quantity = storable.get_full_balance()
        except StockError:
            quantity = Decimal(0)

        return quantity

    def _get_purchase_quantity(self):
        """Returns the quantity to purchase of this component
        """
        if self.industrialized:
            return None

        return self.get_stock_difference()

    def _get_make_quantity(self):
        """Returns the quantity to make of this component
        """
        if not self.industrialized:
            return None

        return self.get_stock_difference()

    def get_subcomponents(self):
        """Returns the subcomponents of this component
        """
        return self.product.get_components()

    def get_stock_difference(self):
        """Returns the difference between the quantity in stock and the
        quantity we need of this component.
        """
        difference = self.needed_quantity - self.stock_quantity
        if difference < 0:
            difference = Decimal(0)
        return difference

    def get_industrialized_str(self):
        if self.industrialized:
            return _(u"Yes")
        return _(u"No")

    def update_values(self):
        """Update the following values:
            - purchase_quantity
            - make_quantity
            - last_quantity

        Based on the needed_quantity.
        """
        if self.industrialized:
            self.last_quantity = self.make_quantity
        else:
            self.last_quantity = self.purchase_quantity

        self.purchase_quantity = self._get_purchase_quantity()
        self.make_quantity = self._get_make_quantity()

    def can_update_quantity(self):
        if self.industrialized:
            if self.make_quantity < 0:
                self.make_quantity = self.last_quantity
                return False
        else:
            if self.purchase_quantity < 0:
                self.purchase_quantity = self.last_quantity
                return False

        return True

    def create_purchase_item(self, order, trans):
        if not self.purchase_quantity:
            return

        sellable = self.product.sellable
        PurchaseItem(sellable=sellable,
                    cost=sellable.cost,
                    quantity=self.purchase_quantity,
                    order=order, connection=trans)

    def can_purchase(self):
        return not self.industrialized and self.purchase_quantity

    def has_valid_purchase_quantity(self):
        return self.get_stock_difference() <= self.purchase_quantity


class ProductionProductSlave(GladeSlaveDelegate):
    gladefile = 'ProductionProductSlave'

    gsignal('added-product', object)
    gsignal('removed-product', object, int)
    gsignal('updated-product', object, int)

    def __init__(self, conn):
        self.conn = conn
        GladeSlaveDelegate.__init__(self, gladefile=self.gladefile)
        self._setup_widgets()

    def _setup_widgets(self):
        products = [(view.get_product_and_category_description(), view)
                     for view in ProductFullStockView\
                         .select(connection=self.conn,
                                 #XXX: find out why just 'category_description'
                                 #       is not working
                                 orderBy='sellable_category.description')]
        self.productscombo.prefill(products)
        self.product_list.set_columns(self._get_columns())

        self._update_widgets()

    def _update_widgets(self):
        can_add = self.productscombo.get_selected() is not None
        can_remove = self.product_list.get_selected() is not None
        self.add_product_button.set_sensitive(can_add)
        self.remove_product_button.set_sensitive(can_remove)

    def _get_columns(self):
        return [Column('code', title=_(u'Code'), data_type=int),
                Column('category', title=_(u'Category'), data_type=str,
                        expand=True, sorted=True),
                Column('description', title=_(u'Description'),
                        data_type=str, expand=True),
                Column('unit', title=_(u'Unit'), data_type=str),
                Column('cost', title=_(u'Cost'), data_type=currency),
                Column('quantity', title=_(u'Quantity'), data_type=Decimal,
                        editable=True),
            ]

    def _get_product_in_list(self, product, iterable):
        for item in iterable:
            if item.product is product:
                return item

    def _add_product(self, product_view):
        production_item = self._get_product_in_list(product_view.product,
                                                    self.product_list)
        if production_item is None:
            production_item = _TemporaryProductionItem(product_view)
            production_item.last_quantity += 1
            self.product_list.append(production_item)
            self.emit('added-product', production_item)
        else:
            self._update_product_quantity(production_item)

    def _remove_product(self, production_item):
        quantity = production_item.quantity
        self.product_list.remove(production_item)
        self.emit('removed-product', production_item, quantity)

    def _update_product_quantity(self, production_item):
        quantity = production_item.quantity
        if quantity < 0:
            production_item.quantity = production_item.last_quantity
            delta = 0
        else:
            delta = quantity - production_item.last_quantity
            production_item.last_quantity = quantity

        self.product_list.update(production_item)
        self.emit('updated-product', production_item, delta)

    #
    # Kiwi Callbacks
    #

    def on_add_product_button__clicked(self, widget):
        selected = self.productscombo.get_selected()
        if selected is not None:
            self._add_product(selected)

    def on_remove_product_button__clicked(self, widget):
        self._remove_product(self.product_list.get_selected())

    def on_productscombo__content_changed(self, widget):
        self._update_widgets()

    def on_product_list__selection_changed(self, widget, object):
        self._update_widgets()

    def on_product_list__cell_edited(self, widget, item, column):
        self._update_product_quantity(item)


class ProductionComponentSlave(GladeSlaveDelegate):
    gladefile = 'ProductionComponentSlave'

    def __init__(self):
        GladeSlaveDelegate.__init__(self, gladefile=self.gladefile)
        self.has_rows = False
        self._setup_widgets()

    def _setup_widgets(self):
        self.component_list.set_columns(self._get_columns())
        self.export_csv_button.set_sensitive(self.has_rows)

    def _get_columns(self):
        return [Column('industrialized_str', title=_(u'Ind.'), data_type=str),
                Column('code', title=_(u'code'), data_type=str),
                Column('category', title=_(u'Category'), data_type=str,
                        sorted=True),
                Column('description', title=_(u'Description'), data_type=str),
                Column('location', title=_(u'Location'), data_type=str),
                Column('needed_quantity', title=_(u'Needed'),
                        data_type=Decimal),
                Column('stock_quantity', _(u'In Stock'), data_type=Decimal),
                Column('to_receive', _(u'To Receive'), data_type=Decimal),
                ColoredColumn('purchase_quantity', _(u'To Purchase'),
                              data_type=Decimal,
                              editable_attribute='not_industrialized',
                              data_func=self._purchase_colorize,
                              use_data_model=True),
                ColoredColumn('make_quantity', title=_(u'To Make'),
                              data_type=Decimal,
                              editable_attribute='industrialized',
                              data_func=self._make_colorize,
                              use_data_model=True),
           ]

    def _purchase_colorize(self, component):
        stock_diff = component.get_stock_difference()
        if component.purchase_quantity < stock_diff:
            return gdk.color_parse("red")
        elif component.purchase_quantity > stock_diff:
            return gdk.color_parse("green")

    def _make_colorize(self, component):
        stock_diff = component.get_stock_difference()
        if component.make_quantity < stock_diff:
            return gdk.color_parse("red")
        elif component.make_quantity > stock_diff:
            return gdk.color_parse("green")

    def _handle_components(self, components, multiplier=Decimal(1)):
        for component in components:
            production_component = None
            for item in self.component_list:
                if item.product is component.component:
                    production_component = item
                    break

            if production_component is None:
                item = _TemporaryProductionItemComponent(component)
                self.component_list.append(item)
            else:
                quantity = component.quantity * multiplier
                production_component.needed_quantity += quantity
                production_component.update_values()
                self.component_list.update(production_component)

            subcomponents = component.component.get_components()
            self._handle_components(subcomponents, multiplier)
            self._clean_component_list()

    def _update_list_component(self, component):
        if not component.can_update_quantity():
            return
        if component.industrialized:
            delta = component.make_quantity - component.last_quantity
            self._handle_components(component.get_subcomponents(), delta)
            component.last_quantity = component.make_quantity
        else:
            self.component_list.update(component)

    def _clean_component_list(self):
        for c in self.component_list:
            if c.needed_quantity:
                continue
            if not (c.purchase_quantity or c.make_quantity):
                self.component_list.remove(c)

    def _run_csv_exporter_dialog(self):
        run_dialog(CSVExporterDialog, self, None,
                   _TemporaryProductionItemComponent, self.component_list)

    #
    # Public API
    #

    def add_components(self, product_components):
        self._handle_components(product_components)

    def remove_components(self, components, quantity):
        self._handle_components(components, -1 * quantity)

    def update_components(self, components, quantity):
        self._handle_components(components, quantity)

    def has_valid_components(self):
        return any([c.can_purchase() for c in self.component_list])

    def get_components(self):
        for component in self.component_list:
            yield component

    #
    # Kiwi Callbacks
    #

    def on_component_list__cell_edited(self, widget, item, column):
        self._update_list_component(item)

    def on_component_list__has_rows(self, widget, value):
        self.has_rows = value
        self.export_csv_button.set_sensitive(self.has_rows)

    def on_export_csv_button__clicked(self, widget):
        self._run_csv_exporter_dialog()


class ProductionDialog(GladeSlaveDelegate):
    title = _('Production Dialog')
    size = (780, 580)
    gladefile = 'ProductionDialog'

    def __init__(self, conn, model=None):
        GladeSlaveDelegate.__init__(self, gladefile=self.gladefile)
        self.main_dialog = BasicWrappingDialog(self, self.title, size=self.size)
        self.main_dialog.enable_window_controls()
        self.main_dialog.ok_button.set_label(_(u'Create _purchase order'))
        self.main_dialog.ok_button.set_sensitive(False)
        self.conn = conn
        self._setup_widgets()

    def _setup_widgets(self):
        self.product_slave = ProductionProductSlave(self.conn)
        self.product_slave.connect(
            'added-product', self._on_production_item__added)
        self.product_slave.connect(
            'removed-product', self._on_production_item__removed)
        self.product_slave.connect(
            'updated-product', self._on_production_item__updated)
        self.attach_slave('products_holder', self.product_slave)

        self.component_slave = ProductionComponentSlave()
        self.attach_slave('components_holder', self.component_slave)

    def _update_widgets(self):
        self.main_dialog.ok_button.set_sensitive(self.component_slave.has_rows)

    def _has_valid_components(self):
        if not self.component_slave.has_valid_components():
            warning(_(u"You don't have any components to purchase"))
            return False

        for component in self.component_slave.get_components():
            if component.can_purchase():
                if not component.has_valid_purchase_quantity():
                    msg = _('The quantity needed of some components is bigger '
                            'than the quantity you will purchase.\n\n'
                            'Would you like to continue the purchase ?')
                    return not yesno(msg, gtk.RESPONSE_NO,
                                     _("Abort purchase"),
                                     _("Continue purchase"))
        return True

    def _create_purchase_order(self, trans):
        supplier = sysparam(trans).SUGGESTED_SUPPLIER
        branch = api.get_current_branch(trans)
        group = PaymentGroup(connection=trans)
        order = PurchaseOrder(supplier=supplier, branch=branch,
                              status=PurchaseOrder.ORDER_PENDING,
                              group=group,
                              connection=trans)

        for component in self.component_slave.get_components():
            component.create_purchase_item(order, trans)
        return order

    #
    # BasicPluggableDialog Callbacks
    #

    def on_cancel(self):
        return False

    def on_confirm(self):
        return True

    def validate_confirm(self):
        if not self._has_valid_components():
            return False
        # Let's create the purchase order here, so the user might create
        # several orders without leave this dialog
        trans = api.new_transaction()
        order = self._create_purchase_order(trans)
        if not order:
            # FIXME: We should close the connection above if this really happens
            return False

        retval = run_dialog(PurchaseWizard, self, trans, order)
        api.finish_transaction(trans, retval)
        trans.close()
        return retval

    #
    # Callbacks
    #

    def _on_production_item__added(self, widget, production_item):
        components = production_item.get_components()
        self.component_slave.add_components(components)
        self._update_widgets()

    def _on_production_item__removed(self, widget, production_item, quantity):
        components = production_item.get_components()
        self.component_slave.remove_components(components, quantity)
        self._update_widgets()

    def _on_production_item__updated(self, widget, production_item, quantity):
        components = production_item.get_components()
        self.component_slave.update_components(components, quantity)
        self._update_widgets()
