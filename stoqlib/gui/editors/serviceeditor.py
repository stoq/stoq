# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2007 Async Open Source <http://www.async.com.br>
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
""" Service item editor implementation """

import datetime

from kiwi.datatypes import currency, ValidationError

from stoqdrivers.enum import TaxType

from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.parameters import sysparam
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.gui.editors.sellableeditor import SellableEditor
from stoqlib.gui.slaves.sellableslave import SellableDetailsSlave
from stoqlib.domain.service import Service
from stoqlib.domain.sellable import (Sellable,
                                     SellableTaxConstant)

_ = stoqlib_gettext


class ServiceItemEditor(BaseEditor):
    model_name = _('Service')
    # SaleItem really, but we send in 'fake' items
    # through the pos interface, isinstance() doesn't
    # work well with duck typing.
    model_type = object
    gladefile = 'ServiceItemEditor'
    proxy_widgets = ('service_name_label',
                     'price',
                     'estimated_fix_date',
                     'notes')
    size = (500, 265)

    def __init__(self, conn, model):
        BaseEditor.__init__(self, conn, model)
        self.service_name_label.set_bold(True)
        self.set_description(model.description)
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
    model_name = _(u'Service')
    model_type = Service
    help_section = 'service'

    def get_taxes(self):
        service_tax = SellableTaxConstant.get_by_type(TaxType.SERVICE,
                                                      self.conn)
        return [(_(u'No tax'), None), (service_tax.description, service_tax)]

    def setup_slaves(self):
        details_slave = SellableDetailsSlave(self.conn, self.model.sellable)
        details_slave.setup_image_slave(self.model)
        self.attach_slave('slave_holder', details_slave)

    def setup_widgets(self):
        self.sellable_notebook.set_tab_label_text(self.sellable_tab,
                                                  _(u'Service'))
        self.consignment_lbl.hide()
        self.consignment_box.hide()
        self.statuses_combo.set_sensitive(True)

    #
    # BaseEditor hooks
    #

    def create_model(self, conn):
        tax_constant = SellableTaxConstant.get_by_type(TaxType.SERVICE, self.conn)
        sellable = Sellable(description='', price=currency(0),
                            tax_constant=tax_constant,
                            status=Sellable.STATUS_AVAILABLE,
                            connection=conn)
        sellable.unit = sysparam(self.conn).SUGGESTED_UNIT
        model = Service(sellable=sellable, connection=conn)
        return model
