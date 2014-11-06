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

import collections
from decimal import Decimal

from kiwi.ui.forms import NumericField, TextField, PriceField
from kiwi.python import Settable

from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.lib.decorators import cached_property
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class PrintLabelEditor(BaseEditor):
    """ This editor is used to gather information to print labels for a
    purchase item
    """
    model_type = object
    title = _(u'Print labels')

    @cached_property()
    def fields(self):
        return collections.OrderedDict(
            code=TextField(_('Code'), proxy=True),
            description=TextField(_('Description'), proxy=True),
            barcode=TextField(_('Barcode'), proxy=True),
            price=PriceField(_('Price'), proxy=True),
            quantity=NumericField(_('Quantity'), proxy=True),
            skip=NumericField(_('Labels to skip'), proxy=True),
        )

    def __init__(self, store, sellable, model=None, max_quantity=None,
                 visual_mode=False):
        self.sellable = sellable
        self.max_quantity = max_quantity
        BaseEditor.__init__(self, store, model, visual_mode)
        self._setup_widgets()

    def _setup_widgets(self):
        for i in [self.code, self.description, self.barcode, self.price]:
            i.set_sensitive(False)
        if self.max_quantity:
            self.quantity.update(self.max_quantity)

    #
    # BaseEditor Hooks
    #

    def create_model(self, store):
        sellable = self.sellable
        return Settable(barcode=sellable.barcode, code=sellable.code,
                        description=sellable.description, price=sellable.price,
                        quantity=Decimal('1'), skip=Decimal('0'))


class SkipLabelsEditor(BaseEditor):
    """ This dialog collects how many spaces should be skipped when printing a
    label
    """
    model_type = object
    title = _('Labels to skip')

    @cached_property()
    def fields(self):
        return collections.OrderedDict(
            skip=NumericField(_('Labels to skip'), proxy=True),
        )

    def __init__(self, store):
        BaseEditor.__init__(self, store, None)

    def create_model(self, store):
        return Settable(skip=Decimal('0'))
