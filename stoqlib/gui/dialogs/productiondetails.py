# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2009 Async Open Source <http://www.async.com.br>
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
## GNU General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
""" Production details dialogs """

from decimal import Decimal

import pango
import gtk
from kiwi.ui.widgets.list import Column, ColoredColumn

from stoqlib.api import api
from stoqlib.domain.inventory import Inventory
from stoqlib.domain.production import ProductionOrder
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.gui.slaves.productionslave import QualityTestResultSlave
from stoqlib.gui.editors.productioneditor import (ProductionItemProducedEditor,
                                                  ProductionMaterialLostEditor,
                                                  ProductionMaterialAllocateEditor,
                                                  )
from stoqlib.gui.printing import print_report
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.reporting.production import ProductionOrderReport

_ = stoqlib_gettext


class ProductionDetailsDialog(BaseEditor):
    gladefile = "ProductionDetailsDialog"
    model_type = ProductionOrder
    title = _("Production Details")
    size = (750, 460)
    hide_footer = True
    proxy_widgets = ('branch',
                     'order_number',
                     'open_date',
                     'close_date',
                     'responsible_name',
                     'status_string', )

    def _setup_widgets(self):
        self.production_items.set_columns(self._get_production_items_columns())
        self.materials.set_columns(self._get_material_columns())
        self.services.set_columns(self._get_service_columns())
        self.produced_items.set_columns(self._get_produced_items_columns())
        self.produced_items.set_selection_mode(gtk.SELECTION_MULTIPLE)

    def _setup_data(self):
        # FIXME: Improve this
        self.production_items.clear()
        self.materials.clear()
        self.services.clear()
        self.produced_items.clear()

        self.production_items.add_list(self.model.get_items())
        self.materials.add_list(self.model.get_material_items())
        self.services.add_list(self.model.get_service_items())
        self.produced_items.add_list(self.model.produced_items)

        self.proxy.update_many(['close_date', 'status_string'])

    def _get_production_items_columns(self):
        return [Column('description',
                       title=_('Description'),
                       data_type=str, expand=True, searchable=True,
                       ellipsize=pango.ELLIPSIZE_END, sorted=True),
                Column('unit_description', _("Unit"),
                       data_type=str, justify=gtk.JUSTIFY_RIGHT),
                Column('quantity', title=_('Quantity'),
                       data_type=Decimal, justify=gtk.JUSTIFY_RIGHT),
                Column('produced', title=_('Produced'),
                       data_type=Decimal, justify=gtk.JUSTIFY_RIGHT),
                Column('lost', title=_('Lost'),
                       data_type=Decimal, justify=gtk.JUSTIFY_RIGHT)]

    def _get_material_columns(self):
        return [Column('description', title=_('Description'),
                       data_type=str, expand=True, searchable=True,
                       ellipsize=pango.ELLIPSIZE_END, sorted=True),
                Column('product.location', _("Location"), data_type=str),
                Column('unit_description', _("Unit"),
                       data_type=str, justify=gtk.JUSTIFY_RIGHT),
                Column('needed', title=_('Needed'),
                       data_type=Decimal, justify=gtk.JUSTIFY_RIGHT),
                Column('allocated', title=_('Allocated'),
                       data_type=Decimal, justify=gtk.JUSTIFY_RIGHT),
                Column('consumed', title=_('Consumed'),
                       data_type=Decimal, justify=gtk.JUSTIFY_RIGHT),
                Column('lost', title=_('Lost'),
                       data_type=Decimal, justify=gtk.JUSTIFY_RIGHT),
                Column('to_purchase', title=_('To Purchase'),
                       data_type=Decimal, justify=gtk.JUSTIFY_RIGHT,
                       visible=False),
                Column('to_make', title=_('To Make'),
                       data_type=Decimal, justify=gtk.JUSTIFY_RIGHT,
                       visible=False)]

    def _get_service_columns(self):
        return [Column('description', _("Description"), data_type=str,
                       expand=True, ellipsize=pango.ELLIPSIZE_END),
                Column('quantity', _("Quantity"),
                       data_type=Decimal, justify=gtk.JUSTIFY_RIGHT),
                Column('unit_description', _("Unit"),
                       data_type=str, justify=gtk.JUSTIFY_RIGHT)]

    def _get_test_result(self, item, quality_test):
        """Gets test result from cache, or fetch from database.
        """
        hit = self._test_result_cache.get((item.id, quality_test.id), -1)
        if hit != -1:
            return hit

        test_result = item.get_test_result(quality_test)
        self._test_result_cache[(item.id, quality_test.id)] = test_result
        return test_result

    def _format_func(self, item, test):
        """Format function for tests columns.

        test is the quality test associated with the column
        """
        test_result = self._get_test_result(item, test)
        if not test_result:
            val = ''
        else:
            val = test_result.result_value
        return val

    def _colorize(self, item, test):
        """Set the color for this test result

        test is the quality test associated with the column
        """
        test_result = self._get_test_result(item, test)
        if not test_result:
            return False
        return not test_result.test_passed

    def _get_produced_items_columns(self):
        # Create a cache for test results, to avoid quering the database for
        # every update.
        self._test_result_cache = dict()

        columns = [Column('serial_number', title=_('Serial Number'),
                          data_type=str, expand=True)]

        # Add one column for each test from each product.
        products = dict()
        for item in self.model.get_items():
            if item.product in products:
                continue
            products[item.product] = 1
            for test in item.product.quality_tests:
                columns.append(
                    ColoredColumn('id',
                                  data_type=str, title=test.description,
                                  format_func=self._format_func,
                                  format_func_data=test,
                                  color='red', data_func=self._colorize,
                                  use_data_model=True))

        columns.extend([
                Column('test_passed', title=_('Tests Passed'),
                       data_type=bool, visible=False),
                Column('entered_stock', title=_('Entered Stock'),
                       data_type=bool, visible=False)])
        return columns

    #
    # BaseEditor hooks
    #

    def setup_proxies(self):
        self._setup_widgets()
        self.proxy = self.add_proxy(self.model, ProductionDetailsDialog.proxy_widgets)
        self._setup_data()

    def setup_slaves(self):
        self.quality_slave = QualityTestResultSlave(self.conn)
        self.quality_slave.connect('test-updated',
                                   self._on_quality__test_updated)
        self.attach_slave('quality_holder', self.quality_slave)

    def has_open_inventory(self):
        has_open = Inventory.has_open(self.conn,
                                      api.get_current_branch(self.conn))
        return bool(has_open)

    #
    #   Actions
    #

    def _run_editor(self, editor_class, item):
        self.conn.savepoint('before_run_editor')
        retval = run_dialog(editor_class, self, self.conn, item)
        if not retval:
            self.conn.rollback_to_savepoint('before_run_editor')
        else:
            self.conn.commit()
            self._setup_data()

    def _produce(self):
        production_item = self.production_items.get_selected()
        self._run_editor(ProductionItemProducedEditor, production_item)

    def _add_lost(self):
        item = self.materials.get_selected()
        self._run_editor(ProductionMaterialLostEditor, item)

    def _allocate(self):
        item = self.materials.get_selected()
        self._run_editor(ProductionMaterialAllocateEditor, item)

    #
    # Kiwi Callbacks
    #

    def _on_quality__test_updated(self, slave, produced_item, quality_test,
                                  test_result):
        self._test_result_cache[(produced_item.id, quality_test.id)] = test_result
        self.produced_items.update(produced_item)

    def on_print_button__clicked(self, widget):
        print_report(ProductionOrderReport, self.model)

    def on_production_items__selection_changed(self, widget, item):
        self.produce_button.set_sensitive(bool(item) and item.can_produce(1)
                                          and not self.has_open_inventory())

    def on_materials__selection_changed(self, widget, item):
        self.lost_button.set_sensitive(bool(item) and
                                       item.can_add_lost(Decimal('0.001')))
        self.allocate_button.set_sensitive(bool(item) and
                    self.model.status == ProductionOrder.ORDER_PRODUCING
                    and not self.has_open_inventory())

    def on_produced_items__selection_changed(self, widget, items):
        products = set()
        for i in items:
            products.add(i.product)

        is_in_qa = self.model.status in (ProductionOrder.ORDER_PRODUCING,
                                         ProductionOrder.ORDER_QA)
        # We can only set test results if only one type of product is selected
        if len(products) == 1 and is_in_qa:
            self.quality_slave.set_item_tests(items, items[0].product)
        else:
            self.quality_slave.set_item_tests([], None)

    def on_lost_button__clicked(self, button):
        self._add_lost()

    def on_allocate_button__clicked(self, button):
        self._allocate()

    def on_produce_button__clicked(self, button):
        self._produce()

    def on_production_items__row_activated(self, list, row):
        if self.produce_button.get_sensitive():
            self._produce()
