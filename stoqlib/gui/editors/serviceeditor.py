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

from kiwi.currency import currency
from kiwi.datatypes import ValidationError

from stoqdrivers.enum import TaxType

from stoqlib.lib.dateutils import localtoday
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.lib.parameters import sysparam
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.gui.editors.sellableeditor import SellableEditor
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
    proxy_widgets = ('sellable_description',
                     'price',
                     'estimated_fix_date',
                     'notes')
    size = (500, 265)

    def __init__(self, store, model):
        BaseEditor.__init__(self, store, model)
        self.sellable_description.set_bold(True)
        self.set_description(model.sellable.description)
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
        if date < localtoday().date():
            return ValidationError(_("Expected receival date must be set to a future date"))


class ServiceEditor(SellableEditor):
    model_name = _(u'Service')
    model_type = Service
    help_section = 'service'

    #
    #  SellableEditor
    #

    def get_taxes(self):
        service_tax = SellableTaxConstant.get_by_type(TaxType.SERVICE,
                                                      self.store)
        return [(_(u'No tax'), None), (service_tax.description, service_tax)]

    def setup_widgets(self):
        for widget in [self.product_type_lbl, self.product_type_str]:
            widget.hide()
        self.sellable_notebook.set_tab_label_text(self.sellable_tab,
                                                  _(u'Service'))

    def create_model(self, store):
        tax_constant = SellableTaxConstant.get_by_type(TaxType.SERVICE, self.store)
        sellable = Sellable(description=u'',
                            price=currency(0),
                            store=store)
        sellable.tax_constant = tax_constant
        sellable.unit_id = sysparam.get_object_id('SUGGESTED_UNIT')
        model = Service(sellable=sellable, store=store)
        return model
