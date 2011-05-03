# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005, 2006 Async Open Source <http://www.async.com.br>
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
""" Editors definitions for sellable"""

import sys

import gtk

from kiwi.datatypes import ValidationError
from kiwi.ui.objectlist import Column
from stoqdrivers.enum import TaxType, UnitType

from stoqlib.database.orm import AND, const
from stoqlib.domain.interfaces import IStorable
from stoqlib.domain.fiscal import CfopData
from stoqlib.domain.sellable import (SellableCategory, Sellable,
                                     SellableUnit,
                                     SellableTaxConstant)
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.base.lists import ModelListDialog
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.gui.search.sellableunitsearch import SellableUnitSearch
from stoqlib.gui.slaves.commissionslave import CommissionSlave
from stoqlib.gui.slaves.sellableslave import OnSaleInfoSlave
from stoqlib.lib.message import info, yesno
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.formatters import get_price_format_str

_ = stoqlib_gettext

#
# Editors
#
class SellableTaxConstantEditor(BaseEditor):
    gladefile = 'SellableTaxConstantEditor'
    model_type = SellableTaxConstant
    model_name = _('Taxes and Tax rates')
    proxy_widgets = ('description',
                     'tax_value')

    def __init__(self, conn, model=None):
        BaseEditor.__init__(self, conn, model)



    #
    # BaseEditor
    #

    def create_model(self, conn):
        return SellableTaxConstant(tax_type=int(TaxType.CUSTOM),
                                   tax_value=None,
                                   description=u'',
                                   connection=conn)

    def on_confirm(self):
        return self.model

    def setup_proxies(self):
        self.proxy = self.add_proxy(self.model,
                                    SellableTaxConstantEditor.proxy_widgets)


class SellableTaxConstantsDialog(ModelListDialog):

    # ModelListDialog
    model_type = SellableTaxConstant
    editor_class = SellableTaxConstantEditor
    size = (500, 300)
    title = _("Taxes")

    # ListDialog
    columns = [
        Column('description', _('Description'), data_type=str,
               width=200),
        Column('value', _('Tax rate'), data_type=str),
    ]

    def selection_changed(self, constant):
        if constant is None:
            return
        is_custom = constant.tax_type == TaxType.CUSTOM
        self.listcontainer.remove_button.set_sensitive(is_custom)
        self.listcontainer.edit_button.set_sensitive(is_custom)

    def delete_model(self, model, trans):
        sellables = Sellable.selectBy(tax_constant=model, connection=trans)
        quantity = sellables.count()
        if quantity > 0:
            msg = _(u"You can't remove this tax, since %d products or "
                    "services are taxed with '%s'." % (
                    quantity, model.get_description()))
            info(msg)
        else:
            SellableTaxConstant.delete(model.id, connection=trans)


class SellablePriceEditor(BaseEditor):
    model_name = _(u'Product Price')
    model_type = Sellable
    gladefile = 'SellablePriceEditor'

    proxy_widgets = ('cost',
                     'markup',
                     'max_discount',
                     'price')

    general_widgets = ('base_markup',)

    def set_widget_formats(self):
        widgets = (self.markup, self.base_markup, self.max_discount)
        for widget in widgets:
            widget.set_data_format(get_price_format_str())

    #
    # BaseEditor hooks
    #

    def get_title(self, *args):
        return _('Price settings')

    def setup_proxies(self):
        self.set_widget_formats()
        self.main_proxy = self.add_proxy(self.model,
                                         SellablePriceEditor.proxy_widgets)
        if self.model.markup is not None:
            return
        sellable = self.model.sellable
        self.model.markup = sellable.get_suggested_markup()
        self.main_proxy.update('markup')

    def setup_slaves(self):
        slave = OnSaleInfoSlave(self.conn, self.model.on_sale_info)
        self.attach_slave('on_sale_holder', slave)

        commission_slave = CommissionSlave(self.conn, self.model)
        self.attach_slave('on_commission_data_holder', commission_slave)
        if self.model.category:
            desc = self.model.category.description
            label = _('Calculate Commission From: %s') % desc
            commission_slave.change_label(label)

    #
    # Kiwi handlers
    #

    def after_price__content_changed(self, entry_box):
        self.handler_block(self.markup, 'changed')
        self.main_proxy.update("markup")
        self.handler_unblock(self.markup, 'changed')

    def after_markup__content_changed(self, spin_button):
        self.handler_block(self.price, 'changed')
        self.main_proxy.update("price")
        self.handler_unblock(self.price, 'changed')

    def on_confirm(self):
        slave = self.get_slave('on_commission_data_holder')
        slave.confirm()
        return self.model

#
# Editors
#


class SellableEditor(BaseEditor):
    """This is a base class for ProductEditor and ServiceEditor and should
    be used when editing sellable objects. Note that sellable objects
    are instances inherited by Sellable."""

    # This must be be properly defined in the child classes
    model_name = None
    model_type = None

    gladefile = 'SellableEditor'
    sellable_tax_widgets = ('tax_constant', 'tax_value',)
    sellable_widgets = ('code',
                        'barcode',
                        'description',
                        'category_combo',
                        'cost',
                        'price',
                        'statuses_combo',
                        'default_sale_cfop',
                        'unit_combo')
    proxy_widgets = (sellable_tax_widgets + sellable_widgets)

    storable_widgets = ('stock_total_lbl',)

    def __init__(self, conn, model=None):
        self._sellable = None
        self._requires_weighing_text = ("<b>%s</b>"
                                        % _(u"This unit type requires "
                                            "weighing"))
        self._status_unavailable_text = ("<b>%s</b>"
                                         % _(u"This status changes "
                                         "automatically when the\n product is "
                                         "purchased or an inicial stock is "
                                         "added."))
        BaseEditor.__init__(self, conn, model)
        self.enable_window_controls()

        # code suggestion
        edit_code_product = sysparam(self.conn).EDIT_CODE_PRODUCT
        self.code.set_sensitive(not edit_code_product)
        if not self.code.read():
            code = u'%d' % self._sellable.id
            self.code.update(code)
        self.setup_widgets()

        self.set_description(
            self.model.sellable.base_sellable_info.description)

        self._setup_delete_close_reopen_button()
        # Add/Edit unit button setup.
        self.add_edit_units.connect('clicked',
                                    self._on_add_edit_units__clicked)

    #
    #  Private API
    #

    def _add_extra_button(self, label, stock=None,
                          callback_func=None, connect_on='clicked'):
        button = self.add_button(label, stock)
        if callback_func:
            button.connect(connect_on, callback_func, label)

    def _setup_delete_close_reopen_button(self):
        if self.model and self._sellable.can_remove():
            self._add_extra_button(_('Remove'), 'gtk-delete',
                                   self._on_delete_button__clicked)
        elif self.model and self._sellable.is_unavailable():
            label = (self._sellable.product and
                     _('Close Product') or _('Close Service'))

            self._add_extra_button(label, None,
                                   self._on_close_sellable_button__clicked)
        elif self.model and self._sellable.is_closed():
            label = (self._sellable.product and
                     _('Reopen Product') or _('Reopen Service'))

            self._add_extra_button(label, None,
                                   self._on_reopen_sellable_button__clicked)

    def _update_unit_combo(self):
        selected_value = self.unit_combo.get_selected()
        # Setup the combo again. There might be new items (or even removed).
        self.setup_unit_combo()
        self.unit_combo.select_item_by_data(selected_value)

    #
    #  Public API
    #

    def add_extra_tab(self, tabname, tabslave):
        self.sellable_notebook.set_show_tabs(True)
        self.sellable_notebook.set_show_border(True)

        event_box = gtk.EventBox()
        event_box.show()
        self.sellable_notebook.append_page(event_box, gtk.Label(tabname))
        self.attach_slave(tabname, tabslave, event_box)

    def set_widget_formats(self):
        for widget in (self.cost, self.price):
            widget.set_adjustment(gtk.Adjustment(lower=0, upper=sys.maxint,
                                                 step_incr=1))
        self.stock_total_lbl.set_data_format('%.02f')
        self.requires_weighing_label.set_size("small")
        self.requires_weighing_label.set_text("")
        self.status_unavailable_label.set_size("small")
        self.status_unavailable_label.set_text("")

    def edit_sale_price(self):
        sellable = self.model.sellable
        result = run_dialog(SellablePriceEditor, self, self.conn, sellable)
        if result:
            self.sellable_proxy.update('price')

    def setup_widgets(self):
        raise NotImplementedError

    def update_requires_weighing_label(self):
        unit = self._sellable.unit
        if unit and unit.unit_index == UnitType.WEIGHT:
            self.requires_weighing_label.set_text(self._requires_weighing_text)
        else:
            self.requires_weighing_label.set_text("")

    def update_status_unavailable_label(self):
        if self.statuses_combo.read() == Sellable.STATUS_UNAVAILABLE:
            self.status_unavailable_label.set_text(
                                                 self._status_unavailable_text)
        else:
            self.status_unavailable_label.set_text("")

    def _update_tax_value(self):
        if not hasattr(self, 'tax_proxy'):
            return
        constant = self.tax_constant.get_selected_data()
        self.tax_proxy.update('tax_constant.tax_value')

    def get_taxes(self):
        """Subclasses may override this method to provide a custom
        tax selection.

        @returns: a list of tuples containing the tax description and a
            L{stoqlib.domain.sellable.SellableTaxConstant} object.
        """
        return []

    #
    # BaseEditor hooks
    #

    def setup_sellable_combos(self):
        category_list = SellableCategory.select(
            SellableCategory.q.categoryID != None,
            connection=self.conn).orderBy('description')

        items = [(cat.get_description(), cat) for cat in category_list]
        self.category_combo.prefill(items)

        self.statuses_combo.prefill(
                    [(v, k) for k, v in Sellable.statuses.items()])
        self.statuses_combo.set_sensitive(False)

        cfop_items = [(item.get_description(), item)
                        for item in CfopData.select(connection=self.conn)]
        cfop_items.insert(0, ('', None))
        self.default_sale_cfop.prefill(cfop_items)

        self.setup_unit_combo()


    def setup_unit_combo(self):
        units = SellableUnit.select(connection=self.conn)
        items = [(_("No unit"), None)]
        items.extend([(unit.description, unit) for unit in units])
        self.unit_combo.prefill(items)

    def setup_tax_constants(self):
        taxes = self.get_taxes()
        self.tax_constant.prefill(taxes)

    def setup_proxies(self):
        self.set_widget_formats()
        self._sellable = self.model.sellable

        self.setup_sellable_combos()
        self.setup_tax_constants()
        self.tax_proxy = self.add_proxy(self._sellable,
                                        SellableEditor.sellable_tax_widgets)

        self.sellable_proxy = self.add_proxy(self._sellable,
                                             SellableEditor.sellable_widgets)

        storable = IStorable(self.model, None)
        if storable is not None:
            self.add_proxy(storable,
                           SellableEditor.storable_widgets)

        self.update_requires_weighing_label()
        self.update_status_unavailable_label()

    #
    # Kiwi handlers
    #

    def _on_delete_button__clicked(self, button, parent_button_label=None):
        msg = _(u"This will delete '%s' from the database. Are you sure?"
                % self._sellable.get_description())
        if not yesno(msg, gtk.RESPONSE_NO, _(u"Delete"), _(u"Don't Delete")):
            return

        self._sellable.remove()
        # We don't call self.confirm since it will call validate_confirm
        self.cancel()
        self.main_dialog.retval = True

    def _on_close_sellable_button__clicked(self, button,
                                           parent_button_label=None):
        msg = _(u"Do you really want to close '%s'?\n"
                u"Please note that when it's closed, you won't be able to "
                u"commercialize it anymore." % self._sellable.get_description())
        if not yesno(msg, gtk.RESPONSE_NO,
                      parent_button_label, _(u"Don't Close")):
            return

        self._sellable.close()
        self.confirm()

    def _on_reopen_sellable_button__clicked(self, button,
                                            parent_button_label=None):
        msg = _(u"Do you really want to reopen '%s'?\n"
                u"Note that when it's opened, you will be able to "
                u"commercialize it again." % self._sellable.get_description())
        if not yesno(msg, gtk.RESPONSE_NO,
                      parent_button_label, _(u"Keep Closed")):
            return

        self._sellable.set_unavailable()
        self.confirm()

    def _on_add_edit_units__clicked(self, button):
        run_dialog(SellableUnitSearch, self, self.conn)
        self._update_unit_combo()

    def on_tax_constant__changed(self, combo):
        self._update_tax_value()

    def on_unit_combo__changed(self, combo):
        self.update_requires_weighing_label()

    def on_sale_price_button__clicked(self, button):
        self.edit_sale_price()

    def on_code__validate(self, widget, value):
        if not value:
            return ValidationError(_(u'The code can not be empty.'))
        if self.model.sellable.check_code_exists(value):
            return ValidationError(_(u'The code %s already exists.') % value)

    def on_barcode__validate(self, widget, value):
        if not value:
            return
        if value and len(value) > 14:
            return ValidationError(_(u'Barcode must have 14 digits or less.'))
        if self.model.sellable.check_barcode_exists(value):
            return ValidationError(_('The barcode %s already exists') % value)

    def on_price__validate(self, entry, value):
        if value <= 0:
           return ValidationError(_("Price cannot be zero or negative"))

    def on_cost__validate(self, entry, value):
        if value <= 0:
           return ValidationError(_("Cost cannot be zero or negative"))

    def on_category_combo__content_changed(self, widget):
        category_cb = self.category_combo.get_text()
        category = SellableCategory.selectOneBy(description=category_cb,
                                                connection=self.conn)
        self.model.category = category
