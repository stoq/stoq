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

from kiwi.datatypes import ValidationError

from stoqlib.api import api
from stoqlib.database.admin import create_main_branch
from stoqlib.domain.person import Person
from stoqlib.exceptions import StoqlibError
from stoqlib.gui.base.dialogs import run_dialog
from stoqlib.gui.editors.baseeditor import BaseEditor
from stoqlib.gui.slaves.addressslave import AddressSlave
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class BranchDialog(BaseEditor):
    """Register new branch after creating a database.

    This dialog is only used after the database is created.
    """
    gladefile = 'BranchDialog'
    person_widgets = ('name',
                      'phone_number',
                      'fax_number')
    company_widgets = ('cnpj',
                       'state_registry')
    proxy_widgets = person_widgets + company_widgets
    model_type = Person

    def __init__(self, store, model=None):
        model = create_main_branch(name=u"", store=store).person

        BaseEditor.__init__(self, store, model, visual_mode=False)
        self._setup_widgets()

    def _update_system_parameters(self, person):
        address = person.get_main_address()
        if not address:
            raise StoqlibError("You should have an address defined at "
                               "this point")

        city = address.city_location.city
        sysparam.set_string(self.store, 'CITY_SUGGESTED', city)

        country = address.city_location.country
        sysparam.set_string(self.store, 'COUNTRY_SUGGESTED', country)

        state = address.city_location.state
        sysparam.set_string(self.store, 'STATE_SUGGESTED', state)

        # Update the fancy name
        self.company_proxy.model.fancy_name = self.person_proxy.model.name

    def _setup_widgets(self):
        self.name.grab_focus()
        self.document_l10n = api.get_l10n_field('company_document')
        self.cnpj_lbl.set_label(self.document_l10n.label)
        self.cnpj.set_mask(self.document_l10n.entry_mask)

    def _setup_slaves(self):
        address = self.model.get_main_address()
        self._address_slave = AddressSlave(self.store, self.model, address)
        self.attach_slave("address_holder", self._address_slave)

    #
    # BaseEditor hooks
    #

    def setup_proxies(self):
        self._setup_widgets()
        self._setup_slaves()
        widgets = self.person_widgets
        self.person_proxy = self.add_proxy(self.model, widgets)

        widgets = self.company_widgets
        model = self.model.company
        if not model is None:
            self.company_proxy = self.add_proxy(model, widgets)

    def on_confirm(self):
        self._update_system_parameters(self.model)

    #
    # Kiwi Callbacks
    #

    def on_cnpj__validate(self, widget, value):
        if not self.document_l10n.validate(value):
            return ValidationError(_('%s is not valid.') % (
                self.document_l10n.label,))


def test():  # pragma: no cover
    ec = api.prepare_test()
    person = run_dialog(BranchDialog, None, ec.store)
    print('RETVAL', person)


if __name__ == '__main__':  # pragma: no cover
    test()
