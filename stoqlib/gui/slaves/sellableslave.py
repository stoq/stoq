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
""" Slaves for sellables """

from kiwi.currency import currency
from kiwi.datatypes import ValidationError
from kiwi.ui.objectlist import Column


from stoqlib.domain.person import ClientCategory
from stoqlib.domain.sellable import ClientCategoryPrice, Sellable
from stoqlib.gui.editors.baseeditor import (BaseRelationshipEditorSlave,
                                            BaseEditorSlave)
from stoqlib.gui.editors.sellableeditor import CategoryPriceEditor
from stoqlib.gui.slaves.imageslaveslave import ImageSlave
from stoqlib.lib.formatters import get_formatted_cost
from stoqlib.lib.message import info
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class SellableDetailsSlave(BaseEditorSlave):
    """This is base slave for product or service details."""
    gladefile = 'SellableDetailsSlave'
    proxy_widgets = ['notes']
    model_type = Sellable
    image_model = None

    def __init__(self, store, model=None, db_form=None, visual_mode=False):
        self.db_form = db_form
        BaseEditorSlave.__init__(self, store, model, visual_mode)
        self._setup_image_slave(model and model.image)

    #
    #  BaseEditorSlave hooks
    #

    def setup_proxies(self):
        self.proxy = self.add_proxy(self.model,
                                    SellableDetailsSlave.proxy_widgets)

    #
    #  Private
    #

    def _setup_image_slave(self, image_model):
        slave = ImageSlave(self.store, image_model, visual_mode=self.visual_mode)
        slave.connect('image-changed', self._on_image_slave__image_changed)
        self.attach_slave('sellable_image_holder', slave)

    #
    #  Callbacks
    #

    def _on_image_slave__image_changed(self, slave, image):
        if image:
            image.description = self.model.get_description()
        self.model.image = image


class CategoryPriceSlave(BaseRelationshipEditorSlave):
    """A slave for changing the suppliers for a product.
    """
    target_name = _(u'Category')
    editor = CategoryPriceEditor
    model_type = ClientCategoryPrice

    def __init__(self, store, sellable, visual_mode=False):
        self._sellable = sellable
        BaseRelationshipEditorSlave.__init__(self, store, visual_mode=visual_mode)

    def get_targets(self):
        cats = self.store.find(ClientCategory).order_by(ClientCategory.name)
        return [(c.get_description(), c) for c in cats]

    def get_relations(self):
        return self._sellable.get_category_prices()

    def _format_markup(self, obj):
        return '%0.2f%%' % obj

    def get_columns(self):
        return [Column('category_name', title=_(u'Category'),
                       data_type=str, expand=True, sorted=True),
                Column('price', title=_(u'Price'), data_type=currency,
                       format_func=get_formatted_cost, width=150),
                Column('markup', title=_(u'Markup'), data_type=str,
                       width=100, format_func=self._format_markup)]

    def create_model(self):
        sellable = self._sellable
        category = self.target_combo.get_selected_data()

        if sellable.get_category_price_info(category):
            product_desc = sellable.get_description()
            info(_(u'%s already have a price for category %s') % (product_desc,
                                                                  category.get_description()))
            return

        model = ClientCategoryPrice(sellable=sellable,
                                    category=category,
                                    price=sellable.price,
                                    max_discount=sellable.max_discount,
                                    store=self.store)
        return model


class OnSaleInfoSlave(BaseEditorSlave):
    """A slave for price and dates information when a certain product
    or service is on sale.
    """
    gladefile = 'OnSaleInfoSlave'
    model_type = Sellable
    proxy_widgets = ('on_sale_price',
                     'on_sale_start_date',
                     'on_sale_end_date')

    #
    # BaseEditorSlave hooks
    #

    def setup_proxies(self):
        self.proxy = self.add_proxy(self.model, self.proxy_widgets)

    #
    # Kiwi callbacks
    #

    def on_on_sale_price__validate(self, entry, value):
        if value < 0:
            return ValidationError(_("Sale price can not be 0"))
