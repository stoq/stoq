# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2009 Async Open Source <http://www.async.com.br>
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
""" Sellable category editors implementation"""

import gtk
from kiwi.datatypes import ValidationError

from stoqlib.api import api
from stoqlib.domain.sellable import SellableCategory, SellableTaxConstant
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.gui.slaves.commissionslave import CategoryCommissionSlave
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class SellableCategoryEditor(BaseEditor):
    gladefile = 'SellableCategoryEditor'
    model_type = SellableCategory
    model_name = _('Category')
    size = (500, 350)
    proxy_widgets = ('description',
                     'suggested_markup',
                     'tax_constant',
                     'category')

    def __init__(self, store, model=None, parent_category=None, visual_mode=False):
        self._parent_category = parent_category
        BaseEditor.__init__(self, store, model, visual_mode)
        self.set_description(self.model.get_description())

    #
    #  Public API
    #

    def add_extra_tab(self, tab_label, slave):
        event_box = gtk.EventBox()
        event_box.set_border_width(6)
        self.category_notebook.append_page(event_box, gtk.Label(tab_label))
        self.attach_slave(tab_label, slave, event_box)
        event_box.show()

    #
    #  BaseEditor
    #

    def create_model(self, store):
        category = store.fetch(self._parent_category)
        return SellableCategory(description=u'',
                                category=category,
                                store=store)

    def setup_slaves(self):
        self.commission_slave = CategoryCommissionSlave(self.store,
                                                        self.model)
        self.commission_slave.change_label(_("Get from parent"))
        self.add_extra_tab(_("Commission"), self.commission_slave)

        self._update_widgets()

    def setup_proxies(self):
        # We need to prefill combobox before to set a proxy, since we want
        # the attribute 'group' be set properly in the combo.
        self._setup_widgets()
        self.proxy = self.add_proxy(
            model=self.model, widgets=SellableCategoryEditor.proxy_widgets)

        if not self.edit_mode and self._parent_category:
            for widget in (self.markup_check, self.tax_check):
                widget.set_active(True)
        elif self.model.category:
            # Update check status. Use 'is None' to differentiate from cases
            # where the value is 0 or something evaluated to False
            self.markup_check.set_active(self.model.suggested_markup is None)
            self.tax_check.set_active(self.model.tax_constant is None)

    def on_confirm(self):
        if self.markup_check.get_active():
            self.model.suggested_markup = None
        if self.tax_check.get_active():
            self.model.tax_constant = None

    #
    #  Private
    #

    def _setup_widgets(self):
        self.tax_constant.prefill(
            api.for_combo(self.store.find(SellableTaxConstant)))

        categories = set(self.store.find(SellableCategory,
                                         SellableCategory.id != self.model.id))
        # Remove all children recursively to avoid creating
        # a circular hierarchy
        categories -= self.model.get_children_recursively()

        self.category.prefill(
            api.for_combo(categories, attr='full_description'))

    def _update_widgets(self):
        category_lbl = self.category.get_selected_label()

        for widget in [self.commission_slave.commission_check_btn,
                       self.markup_check, self.tax_check]:
            widget.set_sensitive(bool(category_lbl))
            if not category_lbl:
                # We are not updating the widget active state directly like
                # it's visibility because we don't want to overwrite the
                # user choices. We set it to false when there is no parent
                # to update to call the callbacks bellow.
                widget.set_active(False)

    #
    #  Callbacks
    #

    def on_markup_check__toggled(self, widget):
        active = widget.get_active()
        self.suggested_markup.set_sensitive(not active)
        if active:
            self.model.suggested_markup = self.model.category.get_markup()
        self.proxy.update('suggested_markup')

    def on_tax_check__toggled(self, widget):
        active = widget.get_active()
        self.tax_constant.set_sensitive(not active)
        if active:
            self.model.tax_constant = self.model.category.get_tax_constant()
        self.proxy.update('tax_constant')

    def on_category__content_changed(self, widget):
        # slaves was not set yet, we have to wait (setup slaves will call
        # _update_widgets
        if hasattr(self, 'commission_slave'):
            self._update_widgets()

    def on_description__validate(self, widget, value):
        if self.model.check_unique_value_exists(SellableCategory.description,
                                                value):
            return ValidationError(_('Category already exists.'))
