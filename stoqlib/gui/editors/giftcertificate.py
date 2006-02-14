# -*- Mode: Python; coding: iso-8859-1 -*-
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
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
## Author(s):   Evandro Vale Miquelito    <evandro@async.com.br>
##
""" Gift Certificate editor implementation """

import gettext

from kiwi.python import Settable

from stoqlib.gui.base.editors import BaseEditor
from stoqlib.lib.validators import get_price_format_str
from stoqlib.gui.slaves.sellable import OnSaleInfoSlave
from stoqlib.domain.interfaces import ISellable
from stoqlib.domain.sellable import BaseSellableInfo
from stoqlib.domain.giftcertificate import (GiftCertificate,
                                            GiftCertificateType,
                                            get_volatile_gift_certificate)

_ = lambda msg: gettext.dgettext('stoqlib', msg)


class GiftCertificateTypeEditor(BaseEditor):
    """Gift certificates type are instances used by gift certificates as
    markers or categories with specific sales information.
    """
    model_name = _('Gift Certificate Type')
    model_type = GiftCertificateType
    gladefile = 'GiftCertificateTypeEditor'
    size = (545, 240)
    proxy_widgets = ('description',
                     'price',
                     'commission',
                     'max_discount')

    # 
    # BaseEditor hooks
    #

    def create_model(self, conn):
        sellable_info = BaseSellableInfo(connection=conn, price=0.0,
                                         description='')
        return self.model_type(connection=conn,
                               base_sellable_info=sellable_info)

    def get_title_model_attribute(self, model):
        return model.base_sellable_info.description

    def setup_proxies(self):
        widgets = [self.commission, self.max_discount]
        for widget in widgets:
            widget.set_data_format(get_price_format_str())
        self.add_proxy(self.model, GiftCertificateTypeEditor.proxy_widgets)

    def setup_slaves(self):
        self.slave = OnSaleInfoSlave(self.conn, self.model.on_sale_info)
        self.attach_slave('on_sale_holder', self.slave)

    def validate_confirm(self):
        if self.model.base_sellable_info.price <= 0:
            msg = _('Gift Certificate price must be greater than zero.')
            self.price.set_invalid(msg)
            return False
        return True


class GiftCertificateEditor(BaseEditor):
    """An editor for gift certificates. A gift certificate can be sold as a
    product through POS application.
    """
    model_name = 'Gift Certificate'
    model_type = Settable
    gladefile = 'GiftCertificateEditor'
    title = _('Add Gift Certificates')
    size = (515, 240)
    proxy_widgets = ('number',
                     'gift_certificate_type',
                     'first_number',
                     'last_number')

    def __init__(self, conn, model=None):
        BaseEditor.__init__(self, conn, model)
        self._setup_widgets()
        self._update_view()

    def _setup_widgets(self):
        self.title_label.set_size('large')
        self.title_label.set_bold(True)
        self.number.grab_focus()

    def _update_view(self):
        single = self.single_check.get_active()
        self.first_number.set_sensitive(not single)
        self.last_number.set_sensitive(not single)
        self.number.set_sensitive(single)

    def _create_gift_certificate(self, sellable_info, code):
        certificate = GiftCertificate(connection=self.conn)
        certificate.addFacet(ISellable, connection=self.conn,
                             code=code, base_sellable_info=sellable_info)

    #
    # BaseEditor hooks
    #

    def create_model(self, conn):
        return get_volatile_gift_certificate()

    def setup_proxies(self):
        table = GiftCertificateType
        certificates = table.get_active_gift_certificates(self.conn)
        descriptions = [c.base_sellable_info.description 
                                    for c in certificates]
        self.gift_certificate_type.set_completion_strings(descriptions,
                                                          list(certificates))
        self.add_proxy(self.model, self.proxy_widgets)


    def on_confirm(self):
        sellable_info = self.model.gift_certificate_type.base_sellable_info
        if not sellable_info:
            raise ValueError('A gift certificate type must be provided '
                             'at this point')
        if self.single_check.get_active():
            self._create_gift_certificate(sellable_info, self.model.number)
        else:
            for number in range(self.model.first_number, 
                                self.model.last_number + 1):
                self._create_gift_certificate(sellable_info, number)
        return True

    #
    # Kiwi callbacks
    #

    def after_single_check__toggled(self, *args):
        self._update_view()

    def after_multiple_check__toggled(self, *args):
        self._update_view()
