# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2009 Async Open Source <http://www.async.com.br>
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
## Author(s):       Ronaldo Maia            <romaia@async.com.br>
##
""" Sale editors """

import sys

import gtk

from kiwi.datatypes import ValidationError

from stoqlib.domain.sale import Sale, SaleItem
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.gui.slaves.taxslave import SaleItemICMSSlave
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class SaleQuoteItemEditor(BaseEditor):
    gladefile = 'SaleQuoteItemEditor'
    model_type = SaleItem
    model_name = _("Sale Quote Item")
    proxy_widgets = ['price',
                     'quantity',
                     'total',]

    def __init__(self, conn, model):
        BaseEditor.__init__(self, conn, model)
        self._setup_widgets()

        sale = self.model.sale
        if sale.status == Sale.STATUS_CONFIRMED:
            self._set_not_editable()

        # not used with sale quote items
        self.sale_quantity_lbl.hide()
        self.return_quantity_lbl.hide()
        self.sale_quantity.hide()
        self.return_quantity.hide()

    def _setup_widgets(self):
        self.sale.set_text("%04d" %  self.model.sale.id)
        self.description.set_text(self.model.sellable.get_description())
        self.quantity.set_adjustment(gtk.Adjustment(lower=1,
                                                    upper=sys.maxint))
        first_page = self.tabs.get_nth_page(0)
        self.tabs.set_tab_label_text(first_page, _(u'Basic'))

        self._setup_taxes()

    def _setup_taxes(self):
        # This taxes are only for products, not services
        if not self.model.sellable.product:
            return

        icms_slave = SaleItemICMSSlave(self.conn, self.model.icms_info)
        self.add_tab(_('ICMS'), icms_slave)

    def add_tab(self, name, slave):
        event_box = gtk.EventBox()
        event_box.show()
        self.tabs.append_page(event_box, gtk.Label(name))
        self.attach_slave(name, slave, event_box)

    def _set_not_editable(self):
        self.price.set_sensitive(False)
        self.quantity.set_sensitive(False)

    def setup_proxies(self):
        self.add_proxy(self.model, SaleQuoteItemEditor.proxy_widgets)

    #
    # Kiwi callbacks
    #

    def on_price__validate(self, widget, value):
        if value <= 0:
            return ValidationError(_(u"The price must be greater than zero."))

        sellable = self.model.sellable
        if not sellable.is_valid_price(value):
            return ValidationError(
                        _(u"Max discount for this product is %.2f%%") %
                            sellable.max_discount)

    def on_quantity__validate(self, widget, value):
        if value <= 0:
            return ValidationError(_(u'The quantity should be greater than '
                                     'zero.'))
