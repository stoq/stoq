# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012 Async Open Source <http://www.async.com.br>
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

"""General slaves for magento"""

from stoqlib.gui.editors.baseeditor import BaseEditorSlave
from stoqlib.lib.translation import stoqlib_gettext

from domain.magentoproduct import MagentoCategory
from domain.magentoconfig import MagentoConfig

_ = stoqlib_gettext


class _TemporaryCategoryModel(object):
    """Temporary category model"""

    def __init__(self, mag_categories):
        self._mag_categories = mag_categories

        self.is_active = mag_categories[0].is_active
        self.description = mag_categories[0].description
        self.meta_keywords = mag_categories[0].meta_keywords

    #
    #  Public API
    #

    def save(self):
        for category in self._mag_categories:
            category.is_active = self.is_active
            category.description = self.description
            category.meta_keywords = self.meta_keywords


class MagentoCategorySlave(BaseEditorSlave):
    """Slave for :class:`stoqlib.gui.editors.SellableCategoryEditor`"""

    title = _("Magento")
    gladefile = 'MagentoCategorySlave'
    model_type = _TemporaryCategoryModel
    proxy_widgets = [
        'is_active',
        'description',
        'meta_keywords',
        ]

    def __init__(self, conn, category, model=None):
        self._category = category
        super(MagentoCategorySlave, self).__init__(conn, model)

    #
    #  BaseEditorSlave
    #

    def setup_proxies(self):
        self._prefill_active_combo()
        self.proxy = self.add_proxy(self.model, self.proxy_widgets)

    def create_model(self, conn):
        mag_categories = []
        for config in MagentoConfig.select(connection=conn):
            mag_category = MagentoCategory.selectOneBy(connection=conn,
                                                       category=self._category,
                                                       config=config)
            if not mag_category:
                mag_category = MagentoCategory(connection=conn,
                                               category=self._category,
                                               config=config)
            mag_categories.append(mag_category)

        return _TemporaryCategoryModel(mag_categories)

    def on_confirm(self):
        self.model.save()
        return super(MagentoCategorySlave, self).on_confirm()

    #
    #  Private
    #

    def _prefill_active_combo(self):
        self.is_active.prefill([
            (_("Get from parent"), None),
            (_("True"), True),
            (_("False"), False),
            ])
