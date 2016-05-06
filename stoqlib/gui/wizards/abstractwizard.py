# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2016 Async Open Source <http://www.async.com.br>
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

import collections
from decimal import Decimal

import gtk
from kiwi.currency import currency
from kiwi.datatypes import ValidationError
from kiwi.ui.objectlist import SummaryLabel
from kiwi.utils import gsignal
from kiwi.python import Settable
from storm.expr import And, Lower

from stoqlib.api import api
from stoqlib.domain.sellable import Sellable
from stoqlib.domain.product import Product, StorableBatch
from stoqlib.domain.service import ServiceView
from stoqlib.domain.views import (ProductFullStockItemView,
                                  ProductComponentView, SellableFullStockView,
                                  ProductFullStockView)
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.base.lists import AdditionListSlave
from stoqlib.gui.base.wizards import WizardStep
from stoqlib.gui.dialogs.batchselectiondialog import BatchDecreaseSelectionDialog
from stoqlib.gui.dialogs.credentialsdialog import CredentialsDialog
from stoqlib.gui.editors.baseeditor import BaseEditorSlave
from stoqlib.gui.events import WizardSellableItemStepEvent
from stoqlib.gui.search.sellablesearch import SellableSearch
from stoqlib.gui.widgets.calculator import CalculatorPopup
from stoqlib.lib.defaults import QUANTITY_PRECISION, MAX_INT
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext


_ = stoqlib_gettext


# FIXME: move this to stoqlib.gui.slaves.sellableslave
class SellableItemSlave(BaseEditorSlave):
    """A slave for selecting sellable items.

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

    and should also provide an acessor that returns the sellable object.

    """
    gsignal('sellable-selected', object)

    gladefile = 'SellableItemSlave'
    proxy_widgets = ('quantity',
                     'unit_label',
                     'cost',
                     'minimum_quantity',
                     'stock_quantity',
                     'sellable_description', )
    summary_label_text = None
    summary_label_column = 'total'
    value_column = 'cost'
    sellable_view = ProductFullStockItemView
    sellable_editable = False
    validate_stock = False

    #: If we should also validate the price of the sellable. (checking if it is
    #: respecting the rules of discount
    validate_price = False

    # FIXME: s/cost/value/
    cost_editable = True
    item_editor = None
    batch_selection_dialog = None

    #: the sellable search class used to select a sellable to add on the list
    sellable_search = SellableSearch

    #: if we should allow to add an item without available batches (no stock).
    #: Can happen when selecting a product that control batches for decrease,
    #: in that case, :meth:`.get_order_item` will receive *batch=None*
    allow_no_batch = False

    #: the mode to pass to the
    #: :class:`stoqlib.gui.widgets.calculator.CalculatorPopup`.
    #: If ``None``, the calculator will not be attached
    calculator_mode = None

    #: If we should add the sellable on the list when activating the barcode.
    #: This is useful when the barcode is supposed to work with barcode
    #: readers. Note that, if the sellable with the given barcode wasn't found,
    #: it'll just be cleared and no error message will be displayed
    add_sellable_on_barcode_activate = False

    #: If we should make visible a label showing the stock and the minimum
    #: quantity of a sellable when one is selected. Note that sellables
    #: without storables (e.g. services) won't have them shown anyway
    stock_labels_visible = True

    def __init__(self, store, parent, model=None, visual_mode=None):
        self.parent = parent

        # The manager is someone who can allow a bigger discount for a sale item
        self.manager = None

        # This is used by add_sellable to know what item represents
        # a given sellable/batch/value so it can be removed without
        # needing to ask for the children class
        self._items_cache = {}

        super(SellableItemSlave, self).__init__(store, model=model,
                                                visual_mode=visual_mode)
        self._setup_widgets()

    #
    #  BaseEditorSlave
    #

    def setup_proxies(self):
        if self.calculator_mode is not None:
            self.calculator_popup = CalculatorPopup(self.cost,
                                                    self.calculator_mode)
        self.proxy = self.add_proxy(None, self.proxy_widgets)

    def setup_slaves(self):
        self.slave = AdditionListSlave(
            self.store, self.get_columns(),
            editor_class=self.item_editor,
            restore_name=self.__class__.__name__,
            visual_mode=self.visual_mode,
            tree=True)

        for item in self.get_saved_items():
            if hasattr(item, 'parent_item'):
                def add_result(result):
                    parent = result.parent_item
                    if parent:
                        add_result(parent)
                    if result not in self.slave.klist:
                        self.slave.klist.append(parent, result)
                    self.slave.klist.expand(result)
                add_result(item)
            else:
                self.slave.klist.append(None, item)

        self.slave.klist.connect('cell-edited', self._on_klist__cell_edited)
        self.slave.connect('before-delete-items',
                           self._on_list_slave__before_delete_items)
        self.slave.connect('after-delete-items',
                           self._on_list_slave__after_delete_items)
        self.slave.connect('on-edit-item', self._on_list_slave__edit_item)
        self.slave.connect('on-add-item', self._on_list_slave__add_item)
        self.attach_slave('list_holder', self.slave)

    def update_visual_mode(self):
        for widget in [self.barcode, self.product_button]:
            widget.set_sensitive(False)

    #
    # Public API
    #

    def add_sellable(self, sellable, parent=None):
        """Add a sellable to the current step

        This will call step.get_order_item to create the correct item for the
        current model, and this created item will be returned.
        """
        quantity = self.get_quantity()
        value = self.cost.read()
        storable = sellable.product_storable
        order_items = []

        batch = self.proxy.model.batch
        # If a batch_number is selected, we will add that item directly. But
        # we need to adjust the batch's type since places using any
        # batch selection different from BatchDecreaseSelectionDialog will
        # be expecting the batch number
        if batch and not issubclass(self.batch_selection_dialog,
                                    BatchDecreaseSelectionDialog):
            batch = batch.batch_number

        if (storable is not None and storable.is_batch and batch is None and
                self.batch_selection_dialog is not None):
            order_items.extend(self.get_batch_order_items(sellable,
                                                          value, quantity))
        else:
            order_item = self.get_order_item(sellable, value, quantity,
                                             batch=batch, parent=parent)
            if order_item is not None:
                order_items.append(order_item)

        for item in order_items:
            if item in self.slave.klist:
                self.slave.klist.update(item)
            else:
                self.slave.klist.append(parent, item)

            product = item.sellable.product
            if product and product.is_package and parent is None:
                for child in self.proxy.model.children:
                    self.add_sellable(child, parent=item)
                    self.slave.klist.expand(item)

        self.update_total()

        if len(order_items):
            self._reset_sellable()

        # After an item is added, reset manager to None so the discount is only
        # authorized for one item at a time.
        self.manager = None

    def remove_items(self, items):
        """Remove items from the current :class:`IContainer`.

        Subclasses can override this if special logic is necessary.
        """
        for item in items:
            # We need to remove the children before remove the parent_item
            self.remove_items(getattr(item, 'children_items', []))
            self.model.remove_item(item)

    def hide_item_addition_toolbar(self):
        self.item_table.hide()

    def hide_add_button(self):
        """Hides the add button
        """
        self.slave.hide_add_button()

    def hide_del_button(self):
        """Hides the del button
        """
        self.slave.hide_del_button()

    def hide_edit_button(self):
        """Hides the edit button
        """
        self.slave.hide_edit_button()

    def get_quantity(self):
        """Returns the quantity of the current model or 1 if there is no model
        :returns: the quantity
        """
        return self.proxy.model and self.proxy.model.quantity or Decimal(1)

    def get_model_item_by_sellable(self, sellable):
        """Returns a model instance by the given sellable.
        :returns: a model instance or None if we could not find the model.
        """
        for item in self.slave.klist:
            if item.sellable == sellable:
                return item

    def get_remaining_quantity(self, sellable, batch=None):
        """Returns the remaining quantity in stock for the given *sellable*

        This will check the remaining quantity in stock taking the
        items on the list in consideration. This is very useful since
        these items still haven't decreased stock.

        :param sellable: the |sellable| to be checked for remaining
            quantity
        :param batch: if not ``None``, the remaining quantity will
            be checked taking the |batch| in consideration
        :return: the remaining quantity or ``None`` if the sellable
            doesn't control stock (e.g. a service)
        """
        if sellable.service or sellable.product_storable is None:
            return None

        total_quatity = sum(i.quantity for i in self.slave.klist if
                            (i.sellable, i.batch) == (sellable, batch))

        branch = self.model.branch
        storable = sellable.product_storable
        # FIXME: It would be better to just use storable.get_balance_for_branch
        # and pass batch=batch there. That would avoid this if
        if batch is not None:
            balance = batch.get_balance_for_branch(branch)
        else:
            balance = storable.get_balance_for_branch(branch)

        return balance - total_quatity

    def update_total(self):
        """Update the summary label with the current total"""
        if self.summary:
            self.summary.update_total()
        self.force_validation()

    def get_parent(self):
        return self.get_toplevel().get_toplevel()

    def validate(self, value):
        self.add_sellable_button.set_sensitive(value
                                               and bool(self.proxy.model)
                                               and bool(self.proxy.model.sellable))

    #
    # Hooks
    #

    def get_sellable_view_query(self):
        """This method should return a tuple containing the viewable that should
        be used and a query that should filter the sellables that can and cannot
        be added to this step.
        """
        return (self.sellable_view,
                Sellable.get_unblocked_sellables_query(self.store))

    def get_order_item(self, sellable, value, quantity, batch=None, parent=None):
        """Adds the sellable to the current model

        This method is called when the user added the sellable in the wizard
        step. Subclasses should implement this method to add the sellable to the
        current model.

        :param sellable: the selected |sellable|
        :param value: the value selected for the sellable
        :param quantity: the quantity selected for the sellable
        :param batch: the batch that was selected for the sellable.
            Note that this argument will only be passed if
            :attr:`.batch_selection_dialog` is defined.
        """
        raise NotImplementedError('This method must be defined on child')

    def get_saved_items(self):
        raise NotImplementedError('This method must be defined on child')

    def get_columns(self):
        raise NotImplementedError('This method must be defined on child')

    def can_add_sellable(self, sellable):
        """Whether we can add a sellable to the list or not

        This is a hook method that gets called when trying to add a
        sellable to the list. It can be rewritten on child classes for
        extra functionality
        :param sellable: the selected sellable
        :returns: True or False (True by default)
        """
        return True

    def get_sellable_model(self, sellable, batch=None):
        """Create a Settable containing multiple information to be used on the
        slave.

        :param sellable: a |sellable| we are adding to wizard
        :returns: a Settable containing some information of the item
        """
        minimum = Decimal(0)
        stock = Decimal(0)
        cost = currency(0)
        quantity = Decimal(0)
        description = u''
        unit_label = u''

        children = {}
        if sellable:
            description = "<b>%s</b>" % api.escape(sellable.get_description())
            cost = getattr(sellable, self.value_column)
            quantity = Decimal(1)
            storable = sellable.product_storable
            unit_label = sellable.unit_description
            if storable:
                minimum = storable.minimum_quantity
                stock = storable.get_balance_for_branch(self.model.branch)

            product = sellable.product
            if product:
                for component in product.get_components():
                    child_sellable = component.component.sellable
                    children[child_sellable] = self.get_sellable_model(child_sellable)

        return Settable(quantity=quantity,
                        cost=cost,
                        sellable=sellable,
                        minimum_quantity=minimum,
                        stock_quantity=stock,
                        sellable_description=description,
                        unit_label=unit_label,
                        batch=batch,
                        children=children)

    def sellable_selected(self, sellable, batch=None):
        """This will be called when a sellable is selected in the combo.
        It can be overriden in a subclass if they wish to do additional
        logic at that point

        :param sellable: the selected |sellable|
        :param batch: the |batch|, if the |sellable| was selected
            by it's batch_number
        """
        has_storable = False

        self.proxy.set_model(self.get_sellable_model(sellable, batch=batch))

        has_sellable = bool(sellable)
        self.add_sellable_button.set_sensitive(has_sellable)
        self.force_validation()
        self.quantity.set_sensitive(has_sellable)
        self.cost.set_sensitive(has_sellable and self.cost_editable)
        self._update_product_labels_visibility(has_storable)

        unit = sellable and sellable.unit
        self.quantity.set_digits(
            QUANTITY_PRECISION if unit and unit.allow_fraction else 0)

        self.emit('sellable-selected', sellable)

    def get_batch_items(self):
        """Get batch items for sellables inside this slave

        :returns: a dict mapping the batch to it's quantity
        """
        batch_items = collections.OrderedDict()
        for item in self.slave.klist:
            if item.batch is None:
                continue
            batch_items.setdefault(item.batch, 0)
            # Sum all quantities of the same batch
            batch_items[item.batch] += item.quantity

        return batch_items

    def get_batch_order_items(self, sellable, value, quantity):
        """Get order items for sellable considering it's |batches|

        By default, this will run :obj:`.batch_selection_dialog` to get
        the batches and their quantities and then call :meth:`.get_order_item`
        on each one.

        :param sellable: a |sellable|
        :param value: the value (e.g. price, cost) of the sellable
        :param quantity: the quantity of the sellable
        """
        order_items = []
        storable = sellable.product_storable
        original_batch_items = self.get_batch_items()
        if issubclass(self.batch_selection_dialog,
                      BatchDecreaseSelectionDialog):
            extra_kw = dict(decreased_batches=original_batch_items)
            available_batches = list(
                storable.get_available_batches(self.model.branch))
            # If there're no available batches (no stock) and we are allowing
            # no batches, add the item without the batch.
            if len(available_batches) == 0 and self.allow_no_batch:
                return [self.get_order_item(sellable, value,
                                            quantity=quantity)]
            # The trivial case, where there's just one batch, and since this
            # is a decrease, we can select it directly
            if len(available_batches) == 1:
                batch = available_batches[0]
                return [self.get_order_item(sellable, value,
                                            quantity=quantity, batch=batch)]
        else:
            extra_kw = dict(original_batches=original_batch_items)

        retval = run_dialog(
            self.batch_selection_dialog, self.get_parent(),
            store=self.store, model=storable, quantity=quantity, **extra_kw)
        retval = retval or {}

        for batch, b_quantity in retval.items():
            order_item = self.get_order_item(sellable, value,
                                             quantity=b_quantity,
                                             batch=batch)
            if order_item is None:
                continue
            order_items.append(order_item)

        return order_items

    def get_extra_discount(self, sellable):
        """Called to get an extra discount for the sellable being added

        Subclasses can implement this to allow some extra discount for the
        sellable being added. For example, one can implement this to
        allow some extra discount based on the unused discount on the
        already added items

        Note that, if you need to get the manager to check for max discount,
        you can use :obj:`.manager`

        :param sellable: the sellable being added
        :returns: the extra discount for the sellable being added,
            or ``None`` if not extra discount should be allowed
        """
        return None

    def get_sellable_search_extra_kwargs(self):
        """Called to get extra args for :attr:`.sellable_search`

        A subclass can override this and return a dict with extra keywords
        to pass to the sellable search defined on the class.

        :returns: a ``dict`` of extra keywords
        """
        return {}

    #
    #  Private
    #
    def _setup_widgets(self):
        self._update_product_labels_visibility(False)
        cost_digits = sysparam.get_int('COST_PRECISION_DIGITS')
        self.quantity.set_sensitive(False)
        # 10 for the length of MAX_INT, 3 for the precision and 1 for comma
        self.quantity.set_max_length(14)
        self.cost.set_sensitive(False)
        # 10 for the length of MAX_INT and 1 for comma
        self.cost.set_max_length(10 + cost_digits + 1)
        self.add_sellable_button.set_sensitive(False)
        self.unit_label.set_bold(True)

        for widget in [self.quantity, self.cost]:
            widget.set_adjustment(gtk.Adjustment(lower=0, upper=MAX_INT,
                                                 step_incr=1))

        self._reset_sellable()
        self._setup_summary()
        self.cost.set_digits(cost_digits)
        self.quantity.set_digits(3)

        self.barcode.grab_focus()
        self.item_table.set_focus_chain([self.barcode,
                                         self.quantity, self.cost,
                                         self.add_sellable_button,
                                         self.product_button])
        self.register_validate_function(self.validate)

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

    def _run_advanced_search(self, search_str=None):
        table, query = self.get_sellable_view_query()
        ret = run_dialog(self.sellable_search, self.get_parent(),
                         self.store,
                         search_spec=table,
                         search_query=query,
                         search_str=search_str,
                         hide_toolbar=not self.sellable_editable,
                         **self.get_sellable_search_extra_kwargs())
        if not ret:
            return

        # We receive different items depend on if we
        # - selected an item in the search
        # - created a new item and it closed the dialog for us
        if not isinstance(ret, (Product, ProductFullStockItemView,
                                ProductComponentView, SellableFullStockView,
                                ServiceView, ProductFullStockView)):
            raise AssertionError(ret)

        sellable = ret.sellable
        if not self.can_add_sellable(sellable):
            return
        if sellable.barcode:
            self.barcode.set_text(sellable.barcode)
        self.sellable_selected(sellable)
        self.quantity.grab_focus()

    def _find_sellable_and_batch(self, text):
        """Find a sellable given a code, barcode or batch_number

        When searching using the code attribute of the sellable, the search will
        be case insensitive.

        :param text: the code, barcode or batch_number
        :returns: The sellable that matches the given barcode or code or
          ``None`` if nothing was found.
        """
        viewable, default_query = self.get_sellable_view_query()

        # FIXME: Put this logic for getting the sellable based on
        # barcode/code/batch_number on domain. Note that something very
        # simular is done on POS app

        # First try barcode, then code since there might be a product
        # with a code equal to another product's barcode
        for attr in [viewable.barcode, viewable.code]:
            query = Lower(attr) == text.lower()
            if default_query:
                query = And(query, default_query)

            result = self.store.find(viewable, query).one()
            if result:
                return result.sellable, None

        # if none of the above worked, try to find by batch number
        query = Lower(StorableBatch.batch_number) == text.lower()
        batch = self.store.find(StorableBatch, query).one()
        if batch:
            sellable = batch.storable.product.sellable
            query = viewable.id == sellable.id
            if default_query:
                query = And(query, default_query)
            # Make sure batch's sellable is in the view
            if not self.store.find(viewable, query).is_empty():
                return sellable, batch

        return None, None

    def _get_sellable_and_batch(self):
        """This method always read the barcode and searches de database.

        If you only need the current selected sellable, use
        self.proxy.model.sellable
        """
        barcode = self.barcode.get_text()
        if not barcode:
            return None, None
        barcode = unicode(barcode, 'utf-8')

        sellable, batch = self._find_sellable_and_batch(barcode)

        if not sellable:
            return None, None
        elif not self.can_add_sellable(sellable):
            return None, None

        return sellable, batch

    def _add_sellable(self):
        sellable = self.proxy.model.sellable
        assert sellable

        sellable = self.store.fetch(sellable)

        self.add_sellable(sellable)
        self.barcode.grab_focus()

    def _reset_sellable(self):
        self.proxy.set_model(None)
        self.sellable_selected(None)

    def _update_product_labels_visibility(self, visible):
        for widget in [self.minimum_quantity_lbl, self.minimum_quantity,
                       self.stock_quantity, self.stock_quantity_lbl]:
            widget.set_visible(self.stock_labels_visible and visible)

    def _try_get_sellable(self):
        """Try to get the sellable based on the barcode typed
        This will try to get the sellable using the barcode the user entered.
           If one is not found, than an advanced search will be displayed for
        the user, and the string he typed in the barcode entry will be
        used to filter the results.
        """
        sellable, batch = self._get_sellable_and_batch()

        if not sellable:
            if self.add_sellable_on_barcode_activate:
                return
            search_str = unicode(self.barcode.get_text())
            self._run_advanced_search(search_str)
            return

        self.sellable_selected(sellable, batch=batch)

        if (self.add_sellable_on_barcode_activate and
                self.add_sellable_button.get_sensitive()):
            self._add_sellable()
        else:
            self.quantity.grab_focus()

    #
    #  Callbacks
    #

    def _on_klist__cell_edited(self, klist, obj, attr):
        self.update_total()

    def _on_list_slave__before_delete_items(self, slave, items):
        self.remove_items(items)
        self.force_validation()

    def _on_list_slave__after_delete_items(self, slave):
        self.update_total()

    def _on_list_slave__add_item(self, slave, item):
        self.update_total()

    def _on_list_slave__edit_item(self, slave, item):
        self.update_total()

    def on_add_sellable_button__clicked(self, button):
        self._add_sellable()

    def on_product_button__clicked(self, button):
        self._try_get_sellable()

    def on_barcode__activate(self, widget):
        self._try_get_sellable()

    def on_quantity__activate(self, entry):
        if self.add_sellable_button.get_sensitive():
            self._add_sellable()

    def on_cost__activate(self, entry):
        if self.add_sellable_button.get_sensitive():
            self._add_sellable()

    def on_quantity__validate(self, entry, value):
        if not self.proxy.model.sellable:
            return

        # Only support positive quantities
        if value <= 0:
            return ValidationError(_(u'The quantity must be positive'))

        # Dont allow numbers bigger than MAX_INT (see stoqlib.lib.defaults)
        if value > MAX_INT:
            return ValidationError(_(u'The quantity cannot be bigger than %s') % MAX_INT)

        sellable = self.proxy.model.sellable
        if sellable and not sellable.is_valid_quantity(value):
            return ValidationError(_(u"This product unit (%s) does not "
                                     u"support fractions.") %
                                   sellable.unit_description)

        storable = sellable.product_storable
        if not self.validate_stock or not storable:
            return
        remaining_quantity = self.get_remaining_quantity(sellable)
        if remaining_quantity is None:
            return
        if value > remaining_quantity:
            return ValidationError(_("This quantity is not available in stock"))

    def on_cost__validate(self, widget, value):
        sellable = self.proxy.model.sellable
        if not sellable:
            return

        # Dont allow numbers bigger than MAX_INT (see stoqlib.lib.defaults)
        if value > MAX_INT:
            return ValidationError(_('Price cannot be bigger than %s') % MAX_INT)

        if value <= 0:
            return ValidationError(_(u'Cost must be greater than zero.'))

        if self.validate_price:
            category = getattr(self.model, 'client_category', None)
            default_price = sellable.get_price_for_category(category)
            if (not sysparam.get_bool('ALLOW_HIGHER_SALE_PRICE') and
                    value > default_price):
                return ValidationError(_(u'The sell price cannot be greater '
                                         'than %s.') % default_price)

            manager = self.manager or api.get_current_user(self.store)
            client = getattr(self.model, 'client', None)
            category = client and client.category
            extra_discount = self.get_extra_discount(sellable)
            valid_data = sellable.is_valid_price(value, category, manager,
                                                 extra_discount=extra_discount)

            if not valid_data['is_valid']:
                return ValidationError(
                    (_(u'Max discount for this product is %.2f%%.') %
                     valid_data['max_discount']))

    def on_cost__icon_press(self, entry, icon_pos, event):
        if icon_pos != gtk.ENTRY_ICON_PRIMARY:
            return

        # No need to check credentials if it is not a price
        if not self.validate_price:
            return

        # Ask for the credentials of a different user that can possibly allow a
        # bigger discount.
        self.manager = run_dialog(CredentialsDialog, self.parent, self.store)
        if self.manager:
            self.cost.validate(force=True)


# FIXME: Instead of doing multiple inheritance, attach
# SellableItemSlave. This will need a lot of refactoring
class SellableItemStep(SellableItemSlave, WizardStep):
    model_type = None

    def __init__(self, wizard, previous, store, model):
        self.wizard = wizard
        WizardStep.__init__(self, previous)
        SellableItemSlave.__init__(self, store, self.wizard, model=model)
        WizardSellableItemStepEvent.emit(self)

    def get_parent(self):
        return self.wizard

    def post_init(self):
        self.barcode.grab_focus()
        self.force_validation()

    def validate(self, value):
        SellableItemSlave.validate(self, value)
        self.wizard.refresh_next(value and bool(len(self.slave.klist)))

    def validate_step(self):
        # FIXME: This should NOT be done here.
        #        Find another way of saving the columns when exiting this
        #        step, without having to depend on next_step, that should
        #        raise NotImplementedError.
        self.slave.save_columns()
        return True

    def get_component(self, parent, sellable):
        product = parent.sellable.product
        for component in product.get_components():
            if component.component.sellable == sellable:
                return component
