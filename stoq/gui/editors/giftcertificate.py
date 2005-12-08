# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005 Async Open Source <http://www.async.com.br>
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
## Author(s):   Evandro Vale Miquelito    <evandro@async.com.br>
##
"""
stoq/gui/editors/giftcertificate.py

    Gift Certificate editor implementation
"""

import gettext

from stoqlib.gui.editors import BaseEditor

from stoq.lib.validators import get_price_format_str
from stoq.gui.editors.sellable import SellableEditor
from stoq.domain.sale import Sale
from stoq.domain.interfaces import ISellable
from stoq.domain.giftcertificate import GiftCertificateItem, GiftCertificate

_ = gettext.gettext


class GiftCertificateItemEditor(BaseEditor):
    """An editor for gift certificate items that are instances tied to a
    certain sale.
    """
    model_name = _('Gift Certificate')
    model_type = GiftCertificateItem
    gladefile = 'GiftCertificateItemEditor'
    size = (550, 200)

    proxy_widgets = ('certificate_number',
                     'amount',
                     'expire_date',
                     'quantity')

    def __init__(self, conn, model, sale, sellable=None):
        if not model:
            self.title = _('New Gift Certificate')
        else:
            self.title = _('Edit Gift Certificate')
        self.sale = sale
        self.sellable = sellable
        BaseEditor.__init__(self, conn, model)

    # 
    # BaseEditor hooks
    #

    def create_model(self, conn):
        if not self.sellable:
            raise ValueError('A sellable attribute is required at this point')
        if not self.sale:
            raise TypeError('This editor (%r) requires a valid Sale object, '
                            'since you don\'t have a model defined.' % self)
        sale = Sale.get(self.sale.id, connection=conn)
        return self.sellable.add_sellable_item(sale, 
                                               price=self.sellable.price,
                                               owner=sale.client)

    def setup_proxies(self):
        self.amount.set_data_format(get_price_format_str())
        self.add_proxy(self.model, GiftCertificateItemEditor.proxy_widgets)

    def validate_confirm(self):
        if self.model.price <= 0:
            msg = _('Gift Certificate amount must be greater than zero.')
            self.amount.set_invalid(msg)
            return False
        return True


class GiftCertificateEditor(SellableEditor):
    """An editor for types of gift certificates"""
    model_name = 'Gift Certificate'
    model_type = GiftCertificate

    def setup_widgets(self):
        self.notes_lbl.set_text(_('Notes:'))
        self.stock_total_lbl.hide()
        self.stock_lbl.hide()

    #
    # BaseEditor hooks
    #

    def create_model(self, conn):
        model = GiftCertificate(connection=conn)
        model.addFacet(ISellable, code='', description='', price=0.0, 
                       connection=conn)
        return model
