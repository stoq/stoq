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

from kiwi.datatypes import ValidationError

from stoqlib.gui.editors.baseeditor import BaseEditorSlave
from stoqlib.gui.slaves.imageslaveslave import ImageSlave
from stoqlib.domain.sellable import Sellable
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


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


class SellableDetailsSlave(BaseEditorSlave):
    """This is base slave for product or service details."""
    gladefile = 'SellableDetailsSlave'
    proxy_widgets = ['notes']
    model_type = Sellable
    image_model = None

    def __init__(self, conn, model=None, db_form=None):
        self.db_form = db_form
        BaseEditorSlave.__init__(self, conn, model)
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
        slave = ImageSlave(self.conn, image_model)
        slave.connect('image-changed', self._on_image_slave__image_changed)
        self.attach_slave('sellable_image_holder', slave)

    #
    #  Callbacks
    #

    def _on_image_slave__image_changed(self, slave, image):
        if image:
            image.description = ('%s #%d' %
                                 (self.model.get_description(), self.model.id))
        self.model.image = image
