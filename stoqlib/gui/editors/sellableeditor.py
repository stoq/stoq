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
""" Editors definitions for sellable"""

import collections

import gtk
from kiwi.datatypes import ValidationError
from kiwi.ui.forms import PercentageField, TextField
from stoqdrivers.enum import TaxType, UnitType

from stoqlib.api import api
from stoqlib.database.exceptions import IntegrityError
from stoqlib.domain.fiscal import CfopData
from stoqlib.domain.sellable import (SellableCategory, Sellable,
                                     SellableUnit,
                                     SellableTaxConstant,
                                     ClientCategoryPrice)
from stoqlib.domain.product import Product
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.dialogs.labeldialog import PrintLabelEditor
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.gui.editors.categoryeditor import SellableCategoryEditor
from stoqlib.gui.slaves.commissionslave import CommissionSlave
from stoqlib.gui.utils.databaseform import DatabaseForm
from stoqlib.gui.utils.printing import print_labels
from stoqlib.lib.decorators import cached_property
from stoqlib.lib.defaults import MAX_INT
from stoqlib.lib.formatters import get_price_format_str, get_formatted_price
from stoqlib.lib.message import yesno, warning
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.stringutils import next_value_for
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext

_DEMO_BAR_CODES = ['2368694135945', '6234564656756', '6985413595971',
                   '2692149835416', '1595843695465', '8596458216412',
                   '9586249534513', '7826592136954', '5892458629421',
                   '1598756984265', '1598756984265', '']
_DEMO_PRODUCT_LIMIT = 30


#
# Editors
#


class SellableTaxConstantEditor(BaseEditor):
    model_type = SellableTaxConstant
    model_name = _('Taxes and Tax rates')

    @cached_property()
    def fields(self):
        return collections.OrderedDict(
            description=TextField(_('Name'), proxy=True, mandatory=True),
            tax_value=PercentageField(_('Value'), proxy=True, mandatory=True),
        )

    #
    # BaseEditor
    #

    def create_model(self, store):
        return SellableTaxConstant(tax_type=int(TaxType.CUSTOM),
                                   tax_value=None,
                                   description=u'',
                                   store=store)


class BasePriceEditor(BaseEditor):
    gladefile = 'SellablePriceEditor'
    proxy_widgets = ['markup', 'cost', 'max_discount', 'price']

    def set_widget_formats(self):
        widgets = (self.markup, self.max_discount)
        for widget in widgets:
            widget.set_data_format(get_price_format_str())

    #
    # BaseEditor hooks
    #

    def get_title(self, *args):
        return _('Price settings')

    def setup_proxies(self):
        self._editing_price = True
        self.markup.update(self.model.markup)

        # These are used to avoid circular updates when changing price or markup
        self._editing_price = False
        self._editing_markup = False

        self.set_widget_formats()
        self.main_proxy = self.add_proxy(self.model, self.proxy_widgets)
        if self.model.markup is not None:
            return
        sellable = self.model.sellable
        self.model.markup = sellable.get_suggested_markup()
        self.main_proxy.update('markup')

    #
    # Kiwi handlers
    #

    def on_price__validate(self, entry, value):
        if value <= 0:
            return ValidationError(_("Price cannot be zero or negative"))

    def after_price__content_changed(self, entry_box):
        # If markup is being edited, dont update the price, or the markup may be
        # programatically changed (if there was any rounding involved)
        if self._editing_markup:
            return

        self._editing_price = True
        self.markup.update(self.model.markup)
        self._editing_price = False

    def after_markup__content_changed(self, spin_button):
        # Like above, if the price is being edited, dont update the markup, or
        # the price may change again.
        if self._editing_price:
            return

        self._editing_markup = True
        self.main_proxy.update("price")
        self._editing_markup = False


class SellablePriceEditor(BasePriceEditor):
    model_name = _(u'Product Price')
    model_type = Sellable

    def setup_slaves(self):
        from stoqlib.gui.slaves.sellableslave import OnSaleInfoSlave
        slave = OnSaleInfoSlave(self.store, self.model)
        self.attach_slave('on_sale_holder', slave)

        commission_slave = CommissionSlave(self.store, self.model)
        self.attach_slave('on_commission_data_holder', commission_slave)
        if self.model.category:
            desc = self.model.category.description
            label = _('Calculate Commission From: %s') % desc
            commission_slave.change_label(label)


class CategoryPriceEditor(BasePriceEditor):
    model_name = _(u'Category Price')
    model_type = ClientCategoryPrice
    sellable_widgets = ('cost', )
    proxy_widgets = ('markup', 'max_discount', 'price')

    def setup_proxies(self):
        self.sellable_proxy = self.add_proxy(self.model.sellable,
                                             self.sellable_widgets)
        BasePriceEditor.setup_proxies(self)


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
    confirm_widgets = ['description', 'cost', 'price']
    ui_form_name = None
    sellable_tax_widgets = ['tax_constant', 'tax_value']
    sellable_widgets = ['code',
                        'barcode',
                        'description',
                        'category_combo',
                        'cost',
                        'price',
                        'status_str',
                        'default_sale_cfop',
                        'unit_combo']
    proxy_widgets = (sellable_tax_widgets + sellable_widgets)

    def __init__(self, store, model=None, visual_mode=False):
        from stoqlib.gui.slaves.sellableslave import CategoryPriceSlave
        is_new = not model
        self._sellable = None
        self._demo_mode = sysparam.get_bool('DEMO_MODE')
        self._requires_weighing_text = (
            "<b>%s</b>" % api.escape(_("This unit type requires weighing")))

        if self.ui_form_name:
            self.db_form = DatabaseForm(self.ui_form_name)
        else:
            self.db_form = None
        BaseEditor.__init__(self, store, model, visual_mode)
        self.enable_window_controls()
        if self._demo_mode:
            self._add_demo_warning()

        # Code suggestion. We need to do this before disabling sensitivity,
        # otherwise, the sellable will not be updated.
        if not self.code.read():
            self._update_default_sellable_code()
        edit_code_product = sysparam.get_bool('EDIT_CODE_PRODUCT')
        self.code.set_sensitive(not edit_code_product and not self.visual_mode)

        self.description.grab_focus()
        self.table.set_focus_chain([self.code,
                                    self.barcode,
                                    self.default_sale_cfop,
                                    self.description,
                                    self.cost_hbox,
                                    self.price_hbox,
                                    self.category_combo,
                                    self.tax_hbox,
                                    self.unit_combo,
                                    ])

        self._print_labels_btn = self.add_button('print_labels', gtk.STOCK_PRINT)
        self._print_labels_btn.connect('clicked', self.on_print_labels_clicked,
                                       'print_labels')
        label = self._print_labels_btn.get_children()[0]
        label = label.get_children()[0].get_children()[1]
        label.set_label(_(u'Print labels'))

        self.setup_widgets()

        if not is_new and not self.visual_mode:
            # Although a sellable can be both removed/closed, we show only one,
            # to avoid having *lots* of buttons. If it's closed, provide a way
            # to reopen it, else, show a delete button if it can be removed
            # or a close button if it can be closed
            if self._sellable.is_closed():
                self._add_reopen_button()
            elif self._sellable.can_remove():
                self._add_delete_button()
            elif self._sellable.can_close():
                self._add_close_button()

        self.set_main_tab_label(self.model_name)
        price_slave = CategoryPriceSlave(self.store, self.model.sellable,
                                         self.visual_mode)
        self.add_extra_tab(_(u'Category Prices'), price_slave)
        self._setup_ui_forms()
        self._update_print_labels()
        self._update_on_price_label()

    def _add_demo_warning(self):
        fmt = _("This is a demostration mode of Stoq, you cannot "
                "create more than %d products.\n"
                "To avoid this limitation, enable production mode.")
        self.set_message(fmt % (_DEMO_PRODUCT_LIMIT))
        if self.store.find(Sellable).count() > _DEMO_PRODUCT_LIMIT:
            self.disable_ok()

    def _add_extra_button(self, label, stock=None,
                          callback_func=None, connect_on='clicked'):
        button = self.add_button(label, stock)
        if callback_func:
            button.connect(connect_on, callback_func, label)

    def _add_delete_button(self):
        self._add_extra_button(_('Remove'), gtk.STOCK_DELETE,
                               self._on_delete_button__clicked)

    def _add_close_button(self):
        if self._sellable.product:
            label = _('Close Product')
        else:
            label = _('Close Service')

        self._add_extra_button(label, None,
                               self._on_close_sellable_button__clicked)

    def _add_reopen_button(self):
        if self._sellable.product:
            label = _('Reopen Product')
        else:
            label = _('Reopen Service')

        self._add_extra_button(label, None,
                               self._on_reopen_sellable_button__clicked)

    def _update_default_sellable_code(self):
        code = Sellable.get_max_value(self.store, Sellable.code)
        self.code.update(next_value_for(code))

    def _update_on_price_label(self):
        if self._sellable.is_on_sale():
            text = _("Currently on sale for %s") % (
                get_formatted_price(self._sellable.on_sale_price), )
        else:
            text = ''

        self.on_sale_lbl.set_text(text)

    def _update_print_labels(self):
        sellable = self.model.sellable
        self._print_labels_btn.set_sensitive(
            all([sellable.code, sellable.barcode,
                 sellable.description, sellable.price]))

    def _setup_ui_forms(self):
        if not self.db_form:
            return

        self.db_form.update_widget(self.code, other=self.code_lbl)
        self.db_form.update_widget(self.barcode, other=self.barcode_lbl)
        self.db_form.update_widget(self.category_combo,
                                   other=self.category_lbl)

    #
    #  Public API
    #

    def set_main_tab_label(self, tabname):
        self.sellable_notebook.set_tab_label(self.sellable_tab,
                                             gtk.Label(tabname))

    def add_extra_tab(self, tabname, tabslave):
        self.sellable_notebook.set_show_tabs(True)
        self.sellable_notebook.set_show_border(True)

        event_box = gtk.EventBox()
        event_box.show()
        self.sellable_notebook.append_page(event_box, gtk.Label(tabname))
        self.attach_slave(tabname, tabslave, event_box)

    def set_widget_formats(self):
        for widget in (self.cost, self.price):
            widget.set_adjustment(gtk.Adjustment(lower=0, upper=MAX_INT,
                                                 step_incr=1))
        self.requires_weighing_label.set_size("small")
        self.requires_weighing_label.set_text("")

    def edit_sale_price(self):
        sellable = self.model.sellable
        self.store.savepoint('before_run_editor_sellable_price')
        result = run_dialog(SellablePriceEditor,
                            self.get_toplevel().get_toplevel(),
                            self.store, sellable)
        if result:
            self._update_on_price_label()
        else:
            self.store.rollback_to_savepoint('before_run_editor_sellable_price')

    def setup_widgets(self):
        raise NotImplementedError

    def update_requires_weighing_label(self):
        unit = self._sellable.unit
        if unit and unit.unit_index == UnitType.WEIGHT:
            self.requires_weighing_label.set_text(self._requires_weighing_text)
        else:
            self.requires_weighing_label.set_text("")

    def _update_tax_value(self):
        if not hasattr(self, 'tax_proxy'):
            return
        self.tax_proxy.update('tax_constant.tax_value')

    def get_taxes(self):
        """Subclasses may override this method to provide a custom
        tax selection.

        :returns: a list of tuples containing the tax description and a
            :class:`stoqlib.domain.sellable.SellableTaxConstant` object.
        """
        return []

    def _fill_categories(self):
        categories = self.store.find(SellableCategory)
        self.category_combo.set_sensitive(any(categories) and not self.visual_mode)
        self.category_combo.prefill(api.for_combo(categories,
                                                  attr='full_description'))

    #
    # BaseEditor hooks
    #

    def update_visual_mode(self):
        self.add_category.set_sensitive(False)
        self.sale_price_button.set_sensitive(False)

    def setup_sellable_combos(self):
        self._fill_categories()
        self.edit_category.set_sensitive(False)

        cfops = CfopData.get_for_sale(self.store)
        self.default_sale_cfop.prefill(api.for_combo(cfops, empty=''))

        self.setup_unit_combo()

    def setup_unit_combo(self):
        units = self.store.find(SellableUnit)
        self.unit_combo.prefill(api.for_combo(units, empty=_('No units')))

    def setup_tax_constants(self):
        taxes = self.get_taxes()
        self.tax_constant.prefill(taxes)

    def setup_proxies(self):
        self.set_widget_formats()
        self._sellable = self.model.sellable

        self.add_category.set_tooltip_text(_("Add a new category"))
        self.edit_category.set_tooltip_text(_("Edit the selected category"))
        self.setup_sellable_combos()
        self.setup_tax_constants()
        self.tax_proxy = self.add_proxy(self._sellable,
                                        SellableEditor.sellable_tax_widgets)

        self.sellable_proxy = self.add_proxy(self._sellable,
                                             SellableEditor.sellable_widgets)

        self.update_requires_weighing_label()

    def setup_slaves(self):
        from stoqlib.gui.slaves.sellableslave import SellableDetailsSlave
        details_slave = SellableDetailsSlave(self.store, self.model.sellable,
                                             visual_mode=self.visual_mode)
        self.attach_slave('slave_holder', details_slave)
        if isinstance(self.model, Product) and self.model.parent is not None:
            details_slave.notes.set_property('sensitive', False)

        # Make everything aligned by pytting notes_lbl on the same size group
        self.left_labels_group.add_widget(details_slave.notes_lbl)

    def _run_category_editor(self, category=None):
        self.store.savepoint('before_run_editor_sellable_category')
        model = run_dialog(SellableCategoryEditor, self, self.store, category)
        if model:
            self._fill_categories()
            self.category_combo.select(model)
        else:
            self.store.rollback_to_savepoint('before_run_editor_sellable_category')

    #
    # Kiwi handlers
    #

    def _on_delete_button__clicked(self, button, parent_button_label=None):
        sellable_description = self._sellable.get_description()
        msg = (_("This will delete '%s' from the database. Are you sure?")
               % sellable_description)
        if not yesno(msg, gtk.RESPONSE_NO, _("Delete"), _("Keep")):
            return

        try:
            self._sellable.remove()
        except IntegrityError as details:
            warning(_("It was not possible to remove '%s'")
                    % sellable_description, str(details))
            return

        # We are doing this by hand instead of calling confirm/cancel because,
        # if we call self.cancel(), the transaction will not be committed. If
        # we call self.confirm(), it will, but some on_confirm hooks (like
        # ProductComponentSlave's one) will try to create other objects and
        # relate them with this product that doesn't exist anymore (we removed
        # them above), resulting in an IntegrityError.
        self.retval = self.model
        self.store.retval = self.retval
        self.main_dialog.close()

    def _on_close_sellable_button__clicked(self, button,
                                           parent_button_label=None):
        msg = (_("Do you really want to close '%s'?\n"
                 "Please note that when it's closed, you won't be able to "
                 "commercialize it anymore.")
               % self._sellable.get_description())
        if not yesno(msg, gtk.RESPONSE_NO,
                     parent_button_label, _("Don't close")):
            return

        self._sellable.close()
        self.confirm()

    def _on_reopen_sellable_button__clicked(self, button,
                                            parent_button_label=None):
        msg = (_("Do you really want to reopen '%s'?\n"
                 "Note that when it's opened, you will be able to "
                 "commercialize it again.") % self._sellable.get_description())
        if not yesno(msg, gtk.RESPONSE_NO,
                     parent_button_label, _("Keep closed")):
            return

        self._sellable.set_available()
        self.confirm()

    def on_category_combo__content_changed(self, category):
        self.edit_category.set_sensitive(bool(category.get_selected()))

    def on_tax_constant__changed(self, combo):
        self._update_tax_value()

    def on_unit_combo__changed(self, combo):
        self.update_requires_weighing_label()

    def on_sale_price_button__clicked(self, button):
        self.edit_sale_price()

    def on_add_category__clicked(self, widget):
        self._run_category_editor()

    def on_edit_category__clicked(self, widget):
        self._run_category_editor(self.category_combo.get_selected())

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
        if self._demo_mode and value not in _DEMO_BAR_CODES:
            return ValidationError(_("Cannot create new barcodes in "
                                     "demonstration mode"))

    def on_price__validate(self, entry, value):
        if value <= 0:
            return ValidationError(_("Price cannot be zero or negative"))

    def on_cost__validate(self, entry, value):
        if value <= 0:
            return ValidationError(_("Cost cannot be zero or negative"))

    def after_description__changed(self, widget):
        self._update_print_labels()

    def after_code__changed(self, widget):
        self._update_print_labels()

    def after_barcode__changed(self, widget):
        self._update_print_labels()

    def after_price__changed(self, widget):
        # This gets called when setting the proxy. It is yet too soon
        # to update the print labels button
        if not hasattr(self, '_print_labels_btn'):
            return
        self._update_print_labels()

    def on_print_labels_clicked(self, button, parent_label_button=None):
        label_data = run_dialog(PrintLabelEditor, None, self.store,
                                self.model.sellable)
        if label_data:
            print_labels(label_data, self.store)


def test_sellable_tax_constant():  # pragma nocover
    ec = api.prepare_test()
    tax_constant = api.sysparam.get_object(ec.store, 'DEFAULT_PRODUCT_TAX_CONSTANT')
    run_dialog(SellableTaxConstantEditor,
               parent=None, store=ec.store, model=tax_constant)
    print(tax_constant)


def test_price_editor():  # pragma nocover
    from decimal import Decimal
    ec = api.prepare_test()
    sellable = ec.create_sellable()
    sellable.cost = Decimal('15.55')
    sellable.price = Decimal('21.50')
    run_dialog(SellablePriceEditor,
               parent=None, store=ec.store, model=sellable)


if __name__ == '__main__':  # pragma nocover
    test_price_editor()
