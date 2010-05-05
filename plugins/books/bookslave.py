# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2010 Async Open Source <http://www.async.com.br>
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
## Author(s):   George Y. Kussumoto  <george@async.com.br>
##
""" Slaves for books """

import sys

import gtk

from kiwi.datatypes import ValidationError

from stoqlib.gui.editors.baseeditor import BaseEditorSlave
from stoqlib.gui.slaves.sellableslave import SellableDetailsSlave
from stoqlib.domain.interfaces import IStorable
from stoqlib.domain.product import Product
from stoqlib.lib.translation import stoqlib_gettext

from booksinterfaces import IBook
from booksdomain import ProductAdaptToBook


_ = stoqlib_gettext


class ProductBookSlave(BaseEditorSlave):
    gladefile = 'ProductBookSlave'
    model_type = ProductAdaptToBook
    proxy_widgets = ['author', 'series', 'edition', 'subject', 'isbn',
                     'language', 'pages', 'synopsis',
                    ]

    def __init__(self, conn, product, model=None):
        self._product = product
        BaseEditorSlave.__init__(self, conn, model)

    def create_model(self, conn):
        model = self._product.addFacet(IBook, connection=conn)
        return model

    def setup_proxies(self):
        #self._setup_widgets()
        self.proxy = self.add_proxy(
            self.model, ProductBookSlave.proxy_widgets)

    def _setup_widgets(self):
        pass
        #self._setup_unit_labels()

        #for widget in [self.minimum_quantity, self.maximum_quantity]:
        #    widget.set_adjustment(
        #        gtk.Adjustment(lower=0, upper=sys.maxint, step_incr=1))



    #
    # Kiwi Callbacks
    #
