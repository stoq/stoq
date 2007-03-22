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
## Author(s): Henrique Romano           <henrique@async.com.br>
##            Evandro Vale Miquelito    <evandro@async.com.br>
##            Bruno Rafael Garcia       <brg@async.com.br>
##
""" Service item editor implementation """

import datetime

from kiwi.datatypes import currency, ValidationError

from stoqdrivers.constants import TAX_SERVICE

from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.gui.editors.sellableeditor import SellableEditor
from stoqlib.domain.interfaces import ISellable
from stoqlib.domain.service import ServiceSellableItem, Service
from stoqlib.domain.sellable import (BaseSellableInfo,
                                     SellableTaxConstant)

_ = stoqlib_gettext


class ServiceItemEditor(BaseEditor):
    model_name = _('Service')
    model_type = ServiceSellableItem
    gladefile = 'ServiceItemEditor'
    proxy_widgets = ('service_name_label',
                     'price',
                     'estimated_fix_date',
                     'notes')
    size = (500, 265)

    def __init__(self, conn, model):
        BaseEditor.__init__(self, conn, model)
        self.service_name_label.set_bold(True)
        self.set_description(model.sellable.base_sellable_info.description)
        self.price.set_sensitive(False)

    #
    # BaseEditor hooks
    #

    def setup_proxies(self):
        self.add_proxy(self.model, ServiceItemEditor.proxy_widgets)

    #
    # Kiwi handlers
    #

    def on_estimated_fix_date__validate(self, widget, date):
        if date < datetime.date.today():
            return ValidationError(_("Expected receival date must be set to a future date"))


class ServiceEditor(SellableEditor):
    model_name = 'Service'
    model_type = Service

    def setup_widgets(self):
        self.notes_lbl.set_text(_('Service details'))
        self.stock_total_lbl.hide()
        self.stock_lbl.hide()

    #
    # BaseEditor hooks
    #

    def create_model(self, conn):
        model = Service(connection=conn)
        sellable_info = BaseSellableInfo(connection=conn,
                                         description='', price=currency(0))
        tax_constant = SellableTaxConstant.get_by_type(TAX_SERVICE, self.conn)
        model.addFacet(ISellable, base_sellable_info=sellable_info,
                       tax_constant=tax_constant,
                       connection=conn)
        return model
