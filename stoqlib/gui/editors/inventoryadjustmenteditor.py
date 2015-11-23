# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2008-2009 Async Open Source <http://www.async.com.br>
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
""" Dialogs for product adjustment """

import collections
from decimal import Decimal

import gtk
from kiwi.datatypes import ValidationError
from kiwi.ui.forms import TextField, NumericField, MultiLineField
from kiwi.ui.objectlist import Column

from stoqlib.domain.inventory import Inventory, InventoryItem
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.gui.fields import CfopField
from stoqlib.lib.decorators import cached_property
from stoqlib.lib.formatters import format_quantity, format_sellable_description
from stoqlib.lib.message import yesno
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class InventoryAdjustmentEditor(BaseEditor):
    title = _(u"Products Adjustment")
    gladefile = "InventoryAdjustmentEditor"
    model_type = Inventory
    size = (750, 450)

    def __init__(self, store, model):
        # Cache the data. this will save all storables, products and sellables
        # in cache, avoiding future quries when populating the list bellow.
        self._data = list(model.get_inventory_data())

        self._has_adjusted_any = False
        BaseEditor.__init__(self, store, model)
        self._setup_widgets()

    #
    #  Private
    #

    def _setup_widgets(self):
        self.main_dialog.ok_button.set_label(_(u'_Finish Inventory'))
        self.main_dialog.cancel_button.set_label(gtk.STOCK_CLOSE)

        company = self.model.branch.person.company
        if company is not None:
            self.branch_lbl.set_text(self.model.branch.get_description())
            self.state_registry_lbl.set_text(company.state_registry)
            self.cnpj_lbl.set_text(company.cnpj)

        self.open_date.set_text(self.model.open_date.strftime("%x"))

        self.inventory_items.set_columns(self._get_columns())
        self.inventory_items.add_list(self.model.get_items())

        if self.model.invoice_number:
            self.invoice_number.set_sensitive(False)

        self._update_widgets()

    def _update_widgets(self):
        if not hasattr(self, 'main_dialog'):
            return

        selection = self.inventory_items.get_selected()
        self.adjust_all_button.set_sensitive(self.invoice_number.is_valid())
        self.adjust_button.set_sensitive(bool(selection) and
                                         not selection.is_adjusted and
                                         self.invoice_number.is_valid())

        # After the first adjustment, the invoice number can not change
        if self._has_adjusted_any:
            self.invoice_number.set_sensitive(False)

    def _get_columns(self):
        return [Column('is_adjusted', title=_(u"Adjusted"),
                       data_type=bool),
                Column('code', title=_(u"Code"), data_type=str,
                       sorted=True),
                Column('description', title=_(u"Description"),
                       data_type=str, expand=True,
                       format_func=self._format_description,
                       format_func_data=True),
                Column('unit_description', title=_(u"Unit"),
                       data_type=str),
                Column('fiscal_description', title=_(u"Fiscal class"),
                       data_type=str, visible=False),
                Column('recorded_quantity', title=_(u"Previous"),
                       data_type=Decimal, format_func=format_quantity),
                Column('counted_quantity', title=_(u"Counted"),
                       data_type=Decimal, format_func=format_quantity),
                # TRANSLATORS: Diff is short for "Difference"
                Column('difference', title=_(u"Diff"),
                       data_type=Decimal, format_func=format_quantity),
                Column('actual_quantity', title=_(u"Actual"),
                       data_type=Decimal, format_func=format_quantity)]

    def _format_description(self, item, data):
        return format_sellable_description(item.product.sellable, item.batch)

    def _run_adjustment_dialog(self, inventory_item):
        self.store.savepoint('before_run_adjustment_dialog')
        retval = run_dialog(InventoryItemAdjustmentEditor, self, self.store,
                            inventory_item, self.model.invoice_number)
        if not retval:
            self.store.rollback_to_savepoint('before_run_adjustment_dialog')
            return

        # The adjustment can be done only once
        self.inventory_items.update(inventory_item)
        self._update_widgets()

    #
    # BaseEditor
    #

    def setup_proxies(self):
        self.proxy = self.add_proxy(self.model, ['invoice_number'])

    def validate_confirm(self):
        if all(i.is_adjusted for i in self.inventory_items):
            return True

        return yesno(_("Some products were not adjusted. By proceeding, you "
                       "will be discarding those products' count and their "
                       "old quantities will still be in the stock. Are you sure?"),
                     gtk.RESPONSE_NO,
                     _("Ignore adjustments"), _("Continue adjusting"))

    def on_confirm(self):
        self.model.close()

    def on_cancel(self):
        if yesno(_("Some products were already adjusted. Do you want to "
                   "save that information or discard them?"),
                 gtk.RESPONSE_NO, _("Save adjustments"), _("Discard adjustments")):
            # change retval to True so the store gets commited
            self.retval = self.model

    #
    # Kiwi Callbacks
    #

    def on_adjust_button__clicked(self, button):
        selected = self.inventory_items.get_selected()
        self._run_adjustment_dialog(selected)

    def on_adjust_all_button__clicked(self, button):
        for item in self.inventory_items:
            if item.is_adjusted:
                continue
            item.actual_quantity = item.counted_quantity
            item.reason = _(u'Automatic adjustment')
            item.adjust(self.model.invoice_number)
            self.inventory_items.update(item)

    def on_inventory_items__row_activated(self, objectlist, item):
        if not self.adjust_button.get_sensitive():
            return

        self._run_adjustment_dialog(item)

    def on_inventory_items__selection_changed(self, objectlist, item):
        self._update_widgets()

    def on_invoice_number__validate(self, widget, value):
        if not 0 < value <= 999999999:
            return ValidationError(
                _("Invoice number must be between 1 and 999999999"))

    def on_invoice_number__validation_changed(self, widget, value):
        self._update_widgets()


class InventoryItemAdjustmentEditor(BaseEditor):
    title = _(u"Product Adjustment")
    hide_footer = False
    model_type = InventoryItem

    @cached_property()
    def fields(self):
        return collections.OrderedDict(
            description=TextField(_("Product"), proxy=True, editable=False),
            recorded_quantity=TextField(_("Previous quantity"), proxy=True,
                                        editable=False),
            counted_quantity=TextField(_("Counted quantity"), proxy=True,
                                       editable=False),
            difference=TextField(_("Difference"), proxy=True, editable=False),
            actual_quantity=NumericField(_("Actual quantity"), proxy=True,
                                         mandatory=True),
            cfop_data=CfopField(_("C.F.O.P"), proxy=True),
            reason=MultiLineField(_("Reason"), proxy=True, mandatory=True),
        )

    def __init__(self, store, model, invoice_number):
        BaseEditor.__init__(self, store, model)
        self._invoice_number = invoice_number

    #
    #  BaseEditor
    #

    def setup_proxies(self):
        self.actual_quantity.update(self.model.counted_quantity)

    def on_confirm(self):
        self.model.adjust(self._invoice_number)
