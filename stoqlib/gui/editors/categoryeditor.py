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

from kiwi.datatypes import ValidationError

from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.gui.slaves.categoryslave import CategoryTributarySituationSlave
from stoqlib.gui.slaves.commissionslave import CategoryCommissionSlave

from stoqlib.lib.parameters import sysparam
from stoqlib.domain.sellable import SellableCategory, SellableTaxConstant

_ = stoqlib_gettext

#
# Helper functions
#


def _validate_category_description(category, description, conn):
    retval = category.check_category_description_exists(description, conn)
    if not retval:
        return ValidationError(_(u'Category already exists.'))

#
# Main editors
#


class BaseSellableCategoryEditor(BaseEditor):
    gladefile = 'BaseSellableCategoryDataSlave'
    model_type = SellableCategory
    model_name = _('Base Category')
    proxy_widgets = ('description',
                     'markup',
                     'tax_constant')
    size = (300, -1)

    def __init__(self, conn, model):
        BaseEditor.__init__(self, conn, model)
        self.set_description(self.model.get_description())

    def create_model(self, conn):
        return SellableCategory(description=u"", category=None, connection=conn)

    def setup_combo(self):
        self.tax_constant.prefill(
            [(c.description, c)
                  for c in SellableTaxConstant.select(connection=self.conn)])

    def setup_proxies(self):
        self.setup_combo()
        self.add_proxy(model=self.model,
                       widgets=BaseSellableCategoryEditor.proxy_widgets)

    def setup_slaves(self):
        slave = CategoryCommissionSlave(self.conn, self.model)
        self.attach_slave('on_commission_data_holder', slave)

    def on_confirm(self):
        slave = self.get_slave('on_commission_data_holder')
        slave.confirm()
        return self.model

    def on_description__validate(self, widget, value):
        return _validate_category_description(self.model, value, self.conn)


class SellableCategoryEditor(BaseEditor):
    gladefile = 'SellableCategoryDataSlave'
    model_type = SellableCategory
    model_name = _('Category')
    proxy_widgets = ('description',
                     'suggested_markup',
                     'category')

    def __init__(self, conn, model):
        BaseEditor.__init__(self, conn, model)
        self.set_description(self.model.get_description())

    def create_model(self, conn):
        return SellableCategory(
            description=u"", category=sysparam(conn).DEFAULT_BASE_CATEGORY,
            connection=conn)

    def get_combo_entries(self):
        return SellableCategory.get_base_categories(self.conn)

    def setup_combo(self):
        self.category.prefill(
            [(c.description, c)
                  for c in self.get_combo_entries()])

    def setup_slaves(self):
        commission_slave = CategoryCommissionSlave(self.conn, self.model)
        self.attach_slave('on_commission_data_holder', commission_slave)
        cat = self.category.get_selected_label()
        commission_slave.change_label(
            _(u'Calculate Commission From: %s') % cat)

        tax_slave = CategoryTributarySituationSlave(self.conn,
                                                    self.model)
        self.attach_slave("on_tax_holder", tax_slave)

    def setup_proxies(self):
        # We need to prefill combobox before to set a proxy, since we want
        # the attribute 'group' be set properly in the combo.
        self.setup_combo()
        self.add_proxy(model=self.model,
                       widgets=SellableCategoryEditor.proxy_widgets)

    def on_category__content_changed(self, widget):
        slave = self.get_slave('on_commission_data_holder')
        cat = self.category.get_selected_label()
        slave.change_label(_('Calculate Commission From: %s') % cat)

    def on_confirm(self):
        slave = self.get_slave('on_commission_data_holder')
        slave.confirm()
        return self.model

    def on_description__validate(self, widget, value):
        return _validate_category_description(self.model, value, self.conn)
