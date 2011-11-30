# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2007 Async Open Source <http://www.async.com.br>
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
""" Abstract wizard and wizard steps definition

Note that a good aproach for all wizards steps defined here is do
not require some specific implementation details for the main wizard. Use
instead signals and interfaces for that.
"""

from decimal import Decimal
import sys

import gtk

from kiwi.datatypes import ValidationError, currency
from kiwi.ui.widgets.list import SummaryLabel
from kiwi.ui.objectlist import SearchColumn
from kiwi.python import Settable

from stoqlib.api import api
from stoqlib.database.orm import AND, ORMObject
from stoqlib.domain.interfaces import IStorable
from stoqlib.domain.sellable import Sellable
from stoqlib.domain.product import Product, ProductSupplierInfo
from stoqlib.domain.service import ServiceView
from stoqlib.domain.views import (ProductFullStockItemView,
                                  ProductComponentView, SellableFullStockView,
                                  ProductWithStockView)
from stoqlib.gui.base.search import SearchEditor
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.base.lists import AdditionListSlave
from stoqlib.gui.base.wizards import WizardEditorStep
from stoqlib.gui.editors.producteditor import ProductEditor
from stoqlib.lib.defaults import sort_sellable_code
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext


_ = stoqlib_gettext


class _SellableSearch(SearchEditor):

    title = _('Item search')
    size = (800, 450)
    has_new_button = True
    editor_class = ProductEditor

    def __init__(self, conn, selection_mode=gtk.SELECTION_BROWSE,
                 search_str=None, query=None, supplier=None,
                 hide_footer=False, double_click_confirm=True,
                 table=None, editable=False,
                 ):
        self._query = query
        self._supplier = supplier
        self._table = table

        SearchEditor.__init__(self, conn, selection_mode=selection_mode,
                              hide_footer=hide_footer, table=table,
                              double_click_confirm=double_click_confirm,
                              hide_toolbar=not editable)
        if search_str:
            self.set_searchbar_search_string(search_str)
            self.search.refresh()

        self.set_ok_label(_('_Select item'))

    #
    # SearchDialog Hooks
    #

    def create_filters(self):
        self.set_text_field_columns(['description', 'barcode',
                                     'category_description', 'code'])
        self.executer.set_query(self.executer_query)

    def executer_query(self, query, having, conn):
        new_query = self._query
        if query:
            new_query = AND(query, new_query)

        return self.search_table.select(new_query, connection=conn)

    def update_widgets(self):
        sellable_view = self.results.get_selected()
        self.ok_button.set_sensitive(bool(sellable_view))

    def get_columns(self):
        columns = [SearchColumn('code', title=_(u'Code'), data_type=str),
                   SearchColumn('barcode', title=_('Barcode'), data_type=str,
                                sort_func=sort_sellable_code, width=80),
                   SearchColumn('category_description', title=_('Category'),
                                data_type=str, width=120),
                   SearchColumn('description', title=_('Description'),
                                data_type=str, expand=True, sorted=True)]

        if 'minimum_quantity' in self._table.columns:
            columns.append(SearchColumn('minimum_quantity',
                                        title=_(u'Minimum Qty'),
                                        data_type=Decimal, visible=False))

        if 'stock' in self._table.columns:
            columns.append(SearchColumn('stock', title=_(u'In Stock'),
                                        data_type=Decimal))

        return columns

    #
    # SearchEditor Hooks
    #

    def get_editor_model(self, model):
        return model.product

    def run_editor(self, obj=None):
        trans = api.new_transaction()
        product = self.run_dialog(self.editor_class, self, trans,
                                 trans.get(obj))

        # This means we are creating a new product. After that, add the
        # current supplier as the supplier for this product
        if (obj is None and product
            and not product.is_supplied_by(self._supplier)):
            ProductSupplierInfo(connection=trans,
                                supplier=self._supplier,
                                product=product,
                                base_cost=product.sellable.cost,
                                is_main_supplier=True)

        if api.finish_transaction(trans, product):
            # If the return value is an ORMObject, fetch it from
            # the right connection
            if isinstance(product, ORMObject):
                product = type(product).get(product.id, connection=self.conn)

            # If we created a new object, confirm the dialog automatically
            if obj is None:
                self.confirm(product)
                return
        trans.close()

        return product

#
# Abstract Wizards for items
#


class SellableItemStep(WizardEditorStep):
    """A wizard item step for sellable orders.

    It defines the following:

      - barcode entry
      - quantity spinbutton
      - cost entry
      - add button
      - find product button
      - sellable objectlist

    Optionally buttons to modify the list

      - Add
      - Remove
      - Edit

    Subclasses should define a sellable_view property and a
    get_sellable_view_query, both used to define what sellables can be added
    to the step.

    The view used should have the following properties:

     - barcode
     - description
     - category_description

    and should also provede an acessor that returns the sellable object.

    """

    gladefile = 'SellableItemStep'
    proxy_widgets = ('quantity',
                     'unit_label',
                     'cost',
                     'minimum_quantity',
                     'stock_quantity',
                     'sellable_description', )
    model_type = None
    table = Sellable
    item_table = None
    summary_label_text = None
    summary_label_column = 'total'
    sellable_view = ProductFullStockItemView
    sellable_editable = False

    def __init__(self, wizard, previous, conn, model):
        WizardEditorStep.__init__(self, conn, wizard, model, previous)
        self.unit_label.set_bold(True)
        for widget in [self.quantity, self.cost]:
            widget.set_adjustment(gtk.Adjustment(lower=0, upper=sys.maxint,
                                                 step_incr=1))
        self._reset_sellable()
        self.cost.set_digits(sysparam(conn).COST_PRECISION_DIGITS)
        self.quantity.set_digits(3)

    # Public API

    def hide_add_button(self):
        """Hides the add button
        """
        self.slave.add_button.hide()

    def hide_edit_button(self):
        """Hides the edit button
        """
        self.slave.hide_edit_button()

    def get_quantity(self):
        """Returns the quantity of the current model or 1 if there is no model
        @returns: the quantity
        """
        return self.proxy.model and self.proxy.model.quantity or Decimal(1)

    def get_model_item_by_sellable(self, sellable):
        """Returns a model instance by the given sellable.
        @returns: a model instance or None if we could not find the model.
        """
        for item in self.slave.klist:
            if item.sellable is sellable:
                return item

    #
    # Hooks
    #

    def get_sellable_view_query(self):
        """This method should return a query that should be used when
        filtering the sellables that can and cannot be added to this step.
        """
        return Sellable.get_unblocked_sellables_query(self.conn)

    def get_order_item(self):
        raise NotImplementedError('This method must be defined on child')

    def get_saved_items(self):
        raise NotImplementedError('This method must be defined on child')

    def get_columns(self):
        raise NotImplementedError('This method must be defined on child')

    def on_product_button__clicked(self, button):
        self._run_advanced_search()

    def can_add_sellable(self, sellable):
        """Whether we can add a sellable to the list or not

        This is a hook method that gets called when trying to add a
        sellable to the list. It can be rewritten on child classes for
        extra functionality
        @param sellable: the selected sellable
        @returns: True or False (True by default)
        """
        return True

    def sellable_selected(self, sellable):
        """This will be called when a sellable is selected in the combo.
        It can be overriden in a subclass if they wish to do additional
        logic at that point
        @param sellable: the selected sellable
        """

        minimum = Decimal(0)
        stock = Decimal(0)
        cost = currency(0)
        quantity = Decimal(0)
        description = u''

        if sellable:
            description = "<b>%s</b>" % sellable.get_description()
            cost = sellable.cost
            quantity = Decimal(1)
            storable = IStorable(sellable.product, None)
            if storable:
                minimum = storable.minimum_quantity
                stock = storable.get_full_balance(self.model.branch)
        else:
            self.barcode.set_text('')

        model = Settable(quantity=quantity,
                         cost=cost,
                         sellable=sellable,
                         minimum_quantity=minimum,
                         stock_quantity=stock,
                         sellable_description=description)

        self.proxy.set_model(model)

        has_sellable = bool(sellable)
        self.add_sellable_button.set_sensitive(has_sellable)
        self.quantity.set_sensitive(has_sellable)
        self.cost.set_sensitive(has_sellable)

    def validate(self, value):
        self.add_sellable_button.set_sensitive(value
                                               and bool(self.proxy.model)
                                               and bool(self.proxy.model.sellable))
        self.wizard.refresh_next(value and bool(len(self.slave.klist)))

    def remove_items(self, items):
        """Remove items from the current L{IContainer}.

        Subclasses can override this if special logic is necessary.
        """
        for item in items:
            self.model.remove_item(item)

    def next_step(self):
        raise NotImplementedError('This method must be defined on child')

    def validate_step(self):
        # FIXME: This should NOT be done here.
        #        Find another way of saving the columns when exiting this
        #        step, without having to depend on next_step, that should
        #        raise NotImplementedError.
        self.slave.save_columns()
        return True

    def post_init(self):
        self.barcode.grab_focus()
        self.item_table.set_focus_chain([self.barcode,
                                         self.quantity, self.cost,
                                         self.add_sellable_button,
                                         self.product_button])
        self.register_validate_function(self.validate)
        self.force_validation()

    def setup_proxies(self):
        self.proxy = self.add_proxy(None, SellableItemStep.proxy_widgets)

    def setup_slaves(self):
        self.slave = AdditionListSlave(
            self.conn, self.get_columns(),
            klist_objects=self.get_saved_items(),
            restore_name=self.__class__.__name__)
        self.slave.connect('before-delete-items',
                           self._on_list_slave__before_delete_items)
        self.slave.connect('after-delete-items',
                           self._on_list_slave__after_delete_items)
        self.slave.connect('on-edit-item', self._on_list_slave__edit_item)
        self.slave.connect('on-add-item', self._on_list_slave__add_item)
        self.attach_slave('list_holder', self.slave)
        self._setup_summary()
        self.quantity.set_sensitive(False)
        self.cost.set_sensitive(False)
        self.add_sellable_button.set_sensitive(False)

    def _setup_summary(self):
        # FIXME: Move this into AdditionListSlave
        if not self.summary_label_column:
            self.summary = None
            return
        self.summary = SummaryLabel(klist=self.slave.klist,
                                    column=self.summary_label_column,
                                    label=self.summary_label_text,
                                    value_format='<b>%s</b>')
        self.summary.show()
        self.slave.list_vbox.pack_start(self.summary, expand=False)

    def _refresh_next(self):
        self.wizard.refresh_next(len(self.slave.klist))

    def _run_advanced_search(self, search_str=None):
        supplier = None
        has_supplier = hasattr(self.model, 'supplier')
        if has_supplier:
            supplier = self.model.supplier
        ret = run_dialog(_SellableSearch, self.wizard,
                         self.conn,
                         search_str=search_str,
                         table=self.sellable_view,
                         supplier=supplier,
                         editable=self.sellable_editable,
                         query=self.get_sellable_view_query()
            )
        if not ret:
            return

        # We receive different items depend on if we
        # - selected an item in the search
        # - created a new item and it closed the dialog for us
        if not isinstance(ret, (Product, ProductFullStockItemView,
                                ProductComponentView, SellableFullStockView,
                                ServiceView, ProductWithStockView)):
            raise AssertionError(ret)

        sellable = ret.sellable
        if not self.can_add_sellable(sellable):
            return
        self.barcode.set_text(sellable.barcode)
        self.sellable_selected(sellable)
        self.quantity.grab_focus()

    def _get_sellable(self):
        """This method always read the barcode and searches de datbase.

        If you only need the currencly selected sellable, use
        self.proxy.model.sellable
        """
        barcode = self.barcode.get_text()
        if not barcode:
            return None

        query = self.sellable_view.q.barcode == barcode
        new_query = self.get_sellable_view_query()
        if new_query:
            query = AND(query, new_query)

        # FIXME: doing list() here is wrong. But there is a bug in one of
        # the queries, that len() == 1 but results.count() == 2.
        results = list(self.sellable_view.select(query,
                                                 connection=self.conn))
        if len(results) != 1:
            return None

        sellable = results[0].sellable
        if not sellable:
            return None
        elif not self.can_add_sellable(sellable):
            return

        return sellable

    def _add_sellable(self):
        sellable = self.proxy.model.sellable
        assert sellable

        self._update_list(sellable)
        self.proxy.set_model(None)
        self.sellable_selected(None)
        self.barcode.grab_focus()

    def _update_list(self, sellable):
        quantity = self.get_quantity()
        cost = sellable.cost
        item = self.get_order_item(sellable, cost, quantity)
        if item is None:
            return

        if item in self.slave.klist:
            self.slave.klist.update(item)
        else:
            self.slave.klist.append(item)

        self._update_total()
        self._reset_sellable()

    def _reset_sellable(self):
        self.proxy.set_model(None)
        self.barcode.set_text('')

    def _update_total(self):
        if self.summary:
            self.summary.update_total()
        self._refresh_next()
        self.force_validation()

    #
    # callbacks
    #

    def _on_list_slave__before_delete_items(self, slave, items):
        self.remove_items(items)
        self._refresh_next()

    def _on_list_slave__after_delete_items(self, slave):
        self._update_total()

    def _on_list_slave__add_item(self, slave, item):
        self._update_total()

    def _on_list_slave__edit_item(self, slave, item):
        self._update_total()

    def on_add_sellable_button__clicked(self, button):
        self._add_sellable()

    def on_barcode__activate(self, widget):
        sellable = self._get_sellable()

        if not sellable:
            search_str = self.barcode.get_text()
            self._run_advanced_search(search_str)
            return

        self.sellable_selected(sellable)
        self.quantity.grab_focus()

    def on_quantity__activate(self, entry):
        if self.add_sellable_button.get_sensitive():
            self._add_sellable()

    def on_cost__activate(self, entry):
        if self.add_sellable_button.get_sensitive():
            self._add_sellable()

    def on_quantity__validate(self, entry, value):
        if not self.proxy.model.sellable:
            return

        # only support positive quantities
        if value <= 0:
            return ValidationError(_(u'The quantity must be positive'))

        sellable = self.proxy.model.sellable
        if sellable and not sellable.is_valid_quantity(value):
            return ValidationError(_(u"This product unit (%s) does not "
                                     u"support fractions.") %
                                     sellable.get_unit_description())

    def on_cost__validate(self, widget, value):
        if not self.proxy.model.sellable:
            return

        if value <= 0:
            return ValidationError(_(u'Cost must be greater than zero.'))
