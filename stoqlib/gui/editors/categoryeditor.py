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
## Author(s):   Evandro Vale Miquelito  <evandro@async.com.br>
##
""" Sellable category editors implementation"""

from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.base.editors import BaseEditor

from stoqlib.lib.parameters import sysparam
from stoqlib.domain.sellable import BaseSellableCategory, SellableCategory

_ = stoqlib_gettext

class BaseSellableCategoryEditor(BaseEditor):
    gladefile = 'BaseSellableCategoryDataSlave'
    model_type = BaseSellableCategory
    model_name = _('Base Category')
    proxy_widgets = ('description',
                     'markup',
                     'commission')
    size = (400, 175)

    def __init__(self, conn, model):
        BaseEditor.__init__(self, conn, model)
        self.set_description(self.model.get_description())

    def create_model(self, conn):
        return BaseSellableCategory(description=u"", connection=conn)

    def setup_proxies(self):
        self.add_proxy(model=self.model,
                       widgets=BaseSellableCategoryEditor.proxy_widgets)


class SellableCategoryEditor(BaseEditor):
    gladefile = 'SellableCategoryDataSlave'
    model_type = SellableCategory
    model_name = _('Category')
    proxy_widgets = ('description',
                     'suggested_markup',
                     'base_category',
                     'commission')

    def __init__(self, conn, model):
        BaseEditor.__init__(self, conn, model)
        self.set_description(self.model.get_description())

    def create_model(self, conn):
        return SellableCategory(
            description=u"", base_category=sysparam(conn).DEFAULT_BASE_CATEGORY,
            connection=conn)

    def setup_combo(self):
        base_category_list = BaseSellableCategory.select(connection=self.conn)
        items = [(base_cat.description, base_cat)
                     for base_cat in base_category_list]
        self.base_category.prefill(items)

    def setup_proxies(self):
        # We need to prefill combobox before to set a proxy, since we want
        # the attribute 'group' be set properly in the combo.
        self.setup_combo()
        self.add_proxy(model=self.model,
                       widgets=SellableCategoryEditor.proxy_widgets)

