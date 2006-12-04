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
## Author(s):   Evandro Vale Miquelito    <evandro@async.com.br>
##
""" Gift Certificate editor implementation """

from kiwi.python import Settable
from kiwi.datatypes import currency

from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.base.editors import BaseEditor
from stoqlib.gui.slaves.sellableslave import OnSaleInfoSlave
from stoqlib.domain.interfaces import ISellable
from stoqlib.domain.sellable import BaseSellableInfo, ASellable
from stoqlib.domain.giftcertificate import (GiftCertificate,
                                            GiftCertificateType,
                                            get_volatile_gift_certificate)

_ = stoqlib_gettext


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

    def __init__(self, conn, model):
        BaseEditor.__init__(self, conn, model)
        self.set_description(self.model.base_sellable_info.description)

    #
    # BaseEditor hooks
    #

    def create_model(self, conn):
        sellable_info = BaseSellableInfo(connection=conn, price=currency(0),
                                         description='')
        return self.model_type(connection=conn,
                               base_sellable_info=sellable_info)

    def setup_proxies(self):
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

    def _create_gift_certificate(self, sellable_info, barcode):
        certificate = GiftCertificate(connection=self.conn)
        certificate.addFacet(ISellable, connection=self.conn,
                             barcode=unicode(barcode),
                             base_sellable_info=sellable_info)

    #
    # BaseEditor hooks
    #

    def create_model(self, conn):
        return get_volatile_gift_certificate()

    def setup_proxies(self):
        table = GiftCertificateType
        certificates = table.get_active_gift_certificates(self.conn)
        items = [(c.base_sellable_info.description, c)
                                    for c in certificates]
        self.gift_certificate_type.prefill(items)
        self.add_proxy(self.model, self.proxy_widgets)

    def validate_confirm(self):
        msg = _(u"The barcode %s already exists")
        if self.single_check.get_active():
            barcode = self.model.number
            if ASellable.check_barcode_exists(barcode):
                self.number.set_invalid(msg % barcode)
                self.main_dialog.enable_ok()
                return False
        else:
            for number in range(self.model.first_number,
                                self.model.last_number + 1):
                barcode = unicode(number)
                if ASellable.check_barcode_exists(barcode):
                    self.first_number.set_invalid(msg % barcode)
                    self.main_dialog.enable_ok()
                    return False
        return True

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
                self._create_gift_certificate(sellable_info, str(number))
        return True

    #
    # Kiwi callbacks
    #

    def after_single_check__toggled(self, *args):
        self._update_view()

    def after_multiple_check__toggled(self, *args):
        self._update_view()
