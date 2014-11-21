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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##
""" Slaves for books """

import gtk
from kiwi.datatypes import ValidationError

from stoqlib.gui.editors.baseeditor import BaseEditorSlave
from stoqlib.lib.defaults import MAX_INT
from stoqlib.lib.countries import get_countries
from stoqlib.lib.translation import stoqlib_gettext

from books.booksdomain import BookPublisher, Book


_ = stoqlib_gettext


class ProductBookSlave(BaseEditorSlave):
    translation_domain = 'stoq'
    domain = 'books'
    gladefile = 'ProductBookSlave'
    title = _(u'Book Details')
    model_type = Book
    proxy_widgets = ['author', 'series', 'edition', 'subject', 'isbn',
                     'language', 'pages', 'synopsis', 'country_combo',
                     'decorative_finish', 'year']

    def __init__(self, store, product, model=None):
        self._product = product
        BaseEditorSlave.__init__(self, store, model)

    def create_model(self, store):
        model = store.find(Book, product=self._product).one()
        if model is None:
            model = Book(product=self._product,
                         store=store)
        return model

    def setup_proxies(self):
        self._setup_widgets()
        self.proxy = self.add_proxy(
            self.model, ProductBookSlave.proxy_widgets)

    def _setup_widgets(self):
        self.country_combo.prefill(get_countries())
        for widget in [self.pages, self.year]:
            widget.set_adjustment(
                gtk.Adjustment(lower=0, upper=MAX_INT, step_incr=1))
        publishers = self.store.find(BookPublisher)
        self.publisher_combo.prefill([(p.person.name, p) for p in publishers])

    #
    # Kiwi Callbacks
    #

    def _positive_validator(self, value):
        if value:
            return
        if value < 0:
            return ValidationError(_(u'The value must be positive.'))

    def on_pages__validate(self, widget, value):
        return self._positive_validator(value)

    def on_year__validate(self, widget, value):
        return self._positive_validator(value)
