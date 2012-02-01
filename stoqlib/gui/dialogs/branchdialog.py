# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006, 2007 Async Open Source <http://www.async.com.br>
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

from decimal import Decimal

from kiwi.datatypes import ValidationError
from kiwi.python import Settable

from stoqlib.api import api
from stoqlib.database.admin import create_main_branch
from stoqlib.exceptions import StoqlibError
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.editors.addresseditor import AddressSlave
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.domain.interfaces import ICompany
from stoqlib.domain.person import Person

_ = stoqlib_gettext


class BranchDialog(BaseEditor):
    """Register new branch after creating a database.

    This dialog is only used after the database is created.
    """
    gladefile = 'BranchDialog'
    person_widgets = ('name',
                      'phone_number',
                      'fax_number')
    tax_widgets = ('icms',
                   'iss',
                   'substitution_icms')
    company_widgets = ('cnpj',
                       'state_registry')
    proxy_widgets = person_widgets + tax_widgets + company_widgets
    model_type = Person

    def __init__(self, trans, model=None):
        model = create_main_branch(name="", trans=trans).person

        self.param = sysparam(trans)
        BaseEditor.__init__(self, trans, model, visual_mode=False)
        self._setup_widgets()

    def _update_system_parameters(self, person):
        icms = self.tax_proxy.model.icms
        self.param.update_parameter('ICMS_TAX', unicode(icms))

        iss = self.tax_proxy.model.iss
        self.param.update_parameter('ISS_TAX', unicode(iss))

        substitution = self.tax_proxy.model.substitution_icms
        self.param.update_parameter('SUBSTITUTION_TAX',
                                    unicode(substitution))

        address = person.get_main_address()
        if not address:
            raise StoqlibError("You should have an address defined at "
                               "this point")

        city = address.city_location.city
        self.param.update_parameter('CITY_SUGGESTED', city)

        country = address.city_location.country
        self.param.update_parameter('COUNTRY_SUGGESTED', country)

        state = address.city_location.state
        self.param.update_parameter('STATE_SUGGESTED', state)

        # Update the fancy name
        self.company_proxy.model.fancy_name = self.person_proxy.model.name

    def _setup_widgets(self):
        self.name.grab_focus()
        self.document_l10n = api.get_l10n_field(self.conn, 'company_document')
        self.cnpj_lbl.set_label(self.document_l10n.label)
        self.cnpj.set_mask(self.document_l10n.entry_mask)

    def _setup_slaves(self):
        address = self.model.get_main_address()
        self._address_slave = AddressSlave(self.conn, self.model, address)
        self.attach_slave("address_holder", self._address_slave)

    #
    # BaseEditor hooks
    #

    def create_model(self, conn):
        return Person(connection=conn)

    def setup_proxies(self):
        self._setup_widgets()
        self._setup_slaves()
        widgets = self.person_widgets
        self.person_proxy = self.add_proxy(self.model, widgets)

        widgets = self.tax_widgets
        iss = Decimal(self.param.ISS_TAX)
        icms = Decimal(self.param.ICMS_TAX)
        substitution = Decimal(self.param.SUBSTITUTION_TAX)
        model = Settable(iss=iss, icms=icms,
                         substitution_icms=substitution)
        self.tax_proxy = self.add_proxy(model, widgets)

        widgets = self.company_widgets
        model = ICompany(self.model, None)
        if not model is None:
            self.company_proxy = self.add_proxy(model, widgets)

    def on_confirm(self):
        self._address_slave.confirm()
        self._update_system_parameters(self.model)
        return self.model

    #
    # Kiwi Callbacks
    #

    def on_icms__validate(self, entry, value):
        if value > 100:
            return ValidationError(_("ICMS can not be greater than 100"))
        if value < 0:
            return ValidationError(_("ICMS can not be less than 0"))

    def on_iss__validate(self, entry, value):
        if value > 100:
            return ValidationError(_("ISS can not be greater than 100"))
        if value < 0:
            return ValidationError(_("ISS can not be less than 0"))

    def on_substitution_icms__validate(self, entry, value):
        if value > 100:
            return ValidationError(_("ICMS Substitution can not be greater "
                                     "than 100"))
        if value < 0:
            return ValidationError(_("ICMS Substitution can not be "
                                     "less than 0"))

    def on_cnpj__validate(self, widget, value):
        if not self.document_l10n.validate(value):
            return ValidationError(_('%s is not valid.') % (
                self.document_l10n.label,))
