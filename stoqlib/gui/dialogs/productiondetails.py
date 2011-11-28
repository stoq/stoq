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
from kiwi.ui.widgets.list import Column

from stoqlib.api import api
from stoqlib.domain.production import ProductionOrder
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.gui.editors.productioneditor import (ProductionItemProducedEditor,
                                                  ProductionMaterialLostEditor,
                                                  ProductionMaterialAllocateEditor,
                                                  ProducedItemQualityTestsDialog)
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
                     'status_string',)

    def _setup_widgets(self):
        self.production_items.set_columns(self._get_production_items_columns())
        self.materials.set_columns(self._get_material_columns())
        self.services.set_columns(self._get_service_columns())
        self.produced_items.set_columns(self._get_produced_items_columns())
        # We should probably allow editing tests results for more than one row
        # at the same time
        #self.produced_items.set_selection_mode(gtk.SELECTION_MULTIPLE)

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
                       ellipsize=pango.ELLIPSIZE_END),
                Column('unit_description', _("Unit"),
                       data_type=str, justify=gtk.JUSTIFY_RIGHT),
                Column('quantity', title=_('Quantity'),
                       data_type=Decimal, justify=gtk.JUSTIFY_RIGHT),
                Column('produced', title=_('Produced'),
                       data_type=Decimal, justify=gtk.JUSTIFY_RIGHT),
                Column('lost', title=_('Lost'),
                       data_type=Decimal, justify=gtk.JUSTIFY_RIGHT),]

    def _get_material_columns(self):
        return [Column('description', title=_('Description'),
                       data_type=str, expand=True, searchable=True,
                       ellipsize=pango.ELLIPSIZE_END),
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
                       visible=False),]

    def _get_service_columns(self):
        return [Column('description', _("Description"), data_type=str,
                       expand=True, ellipsize=pango.ELLIPSIZE_END),
                Column('quantity', _("Quantity"),
                       data_type=Decimal, justify=gtk.JUSTIFY_RIGHT),
                Column('unit_description', _("Unit"),
                       data_type=str, justify=gtk.JUSTIFY_RIGHT),]

    def _get_produced_items_columns(self):
        return [Column('serial_number',
                       title=_('Serial Number'),
                       data_type=str, expand=True),
                Column('test_passed', title=_('Tests Passed'),
                       data_type=bool),
                Column('entered_stock', title=_('Entered Stock'),
                       data_type=bool),
                ]

    #
    # BaseEditor hooks
    #

    def setup_proxies(self):
        self._setup_widgets()
        self.proxy = self.add_proxy(self.model, ProductionDetailsDialog.proxy_widgets)
        self._setup_data()

    #
    #   Actions
    #

    def _run_editor(self, editor_class, item):
        trans = api.new_transaction()
        model = trans.get(item)
        retval = run_dialog(editor_class, self, self.conn, model)
        if api.finish_transaction(trans, retval):
            self._setup_data()
        trans.close()

    def _produce(self):
        production_item = self.production_items.get_selected()
        self._run_editor(ProductionItemProducedEditor, production_item)

    def _add_lost(self):
        item = self.materials.get_selected()
        self._run_editor(ProductionMaterialLostEditor, item)

    def _allocate(self):
        item = self.materials.get_selected()
        self._run_editor(ProductionMaterialAllocateEditor, item)

    def _test(self):
        trans = api.new_transaction()
        produced_item = self.produced_items.get_selected()
        model = trans.get(produced_item)
        run_dialog(ProducedItemQualityTestsDialog, self, trans, model)
        api.finish_transaction(trans, True)
        self._setup_data()
        trans.close()


    #
    # Kiwi Callbacks
    #

    def on_print_button__clicked(self, widget):
        print_report(ProductionOrderReport, self.model)

    def on_production_items__selection_changed(self, widget, item):
        self.produce_button.set_sensitive(bool(item) and item.can_produce(1))

    def on_materials__selection_changed(self, widget, item):
        self.lost_button.set_sensitive(bool(item) and item.can_add_lost(1))
        self.allocate_button.set_sensitive(bool(item) and
                    item.order.status == ProductionOrder.ORDER_PRODUCING)

    def on_produced_items__selection_changed(self, widget, item):
        self.tests_button.set_sensitive(bool(item))

    def on_lost_button__clicked(self, button):
        self._add_lost()

    def on_allocate_button__clicked(self, button):
        self._allocate()

    def on_produce_button__clicked(self, button):
        self._produce()

    def on_production_items__row_activated(self, list, row):
        if self.produce_button.get_sensitive():
            self._produce()

    def on_tests_button__clicked(self, button):
        self._test()

    def on_produced_items__row_activated(self, list, row):
        if self.tests_button.get_sensitive():
            self._test()
