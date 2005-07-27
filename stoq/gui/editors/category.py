# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2004 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU General Public License for more details.
##
## You should have received a copy of the GNU General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
"""
stoq/gui/editors/category.py:

    Sellable category editors implementation.
"""

from stoqlib.gui.editors import BaseEditor

from stoq.lib.parameters import sysparam
from stoq.domain.sellable import (AbstractSellableCategory,
                                  BaseSellableCategory,
                                  SellableCategory)



class BaseSellableCategoryEditor(BaseEditor):
    title = _('Sellable Base Category Editor')
    gladefile = 'BaseSellableCategoryDataSlave'
    model_type = BaseSellableCategory
    widgets = ('description',
               'markup')

    def __init__(self, conn, model=None):
        if not model:
            table = AbstractSellableCategory
            category_data = table(connection=conn, description='')
            model = BaseSellableCategory(connection=conn, 
                                         category_data=category_data)

        BaseEditor.__init__(self, conn=conn, model=model)

    def setup_proxies(self):
        self.add_proxy(model=self.model, widgets=self.widgets)


class SellableCategoryEditor(BaseEditor):
    title = _('Sellable Category Editor')
    gladefile = 'SellableCategoryDataSlave'
    model_type = SellableCategory
    widgets = ('description',
               'suggested_markup',
               'base_category')

    def __init__(self, conn, model=None):
        if not model:
            suggested_base_cat = sysparam(conn).DEFAULT_BASE_CATEGORY

            table = AbstractSellableCategory
            category_data = table(connection=conn, description='')

            table = SellableCategory
            model = table(connection=conn,
                          base_category=suggested_base_cat,
                          category_data=category_data)

        BaseEditor.__init__(self, conn=conn, model=model)

    def setup_combo(self):
        table = BaseSellableCategory
        base_category_list = table.select(connection=self.conn)
        items = [(base_cat.category_data.description, base_cat)
                 for base_cat in base_category_list]

        self.base_category.prefill(items)

    def setup_proxies(self):
        # We need to prefill combobox before to set a proxy, since we want
        # the attribute 'group' be set properly in the combo.
        self.setup_combo()

        self.add_proxy(model=self.model, widgets=self.widgets)
