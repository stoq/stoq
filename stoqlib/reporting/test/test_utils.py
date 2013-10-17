# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013 Async Open Source <http://www.async.com.br>
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
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

import mock

from stoqlib.domain.test.domaintest import DomainTest
from stoqlib.lib.formatters import format_phone_number
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.reporting.utils import get_logo_data, get_header_data
from stoqlib.database.runtime import get_current_branch

_ = stoqlib_gettext


class TestUtils(DomainTest):
    def test_get_logo_data(self):
        image = self.create_image()
        image.image = 'foobar'
        sysparam.set_object(self.store, 'CUSTOM_LOGO_FOR_REPORTS', image)
        data = get_logo_data(self.store)
        self.assertEquals(data, 'data:image/png;base64,Zm9vYmFy')

    def test_get_header_data(self):
        branch = get_current_branch(self.store)
        person = branch.person
        company = person.company
        main_address = person.get_main_address()
        person.email = u'foo@bar'
        person.mobile_number = u'998765432'
        with mock.patch('stoqlib.reporting.utils.get_default_store') as ds:
            ds.return_value = self.store
            data = get_header_data()

        address = ' - '.join([main_address.get_address_string(),
                              main_address.postal_code,
                              main_address.get_city(),
                              main_address.get_state()])
        contact = ' - '.join([format_phone_number(person.phone_number),
                              format_phone_number(person.mobile_number),
                              _("Fax: %s") % format_phone_number(person.fax_number),
                              person.email])
        register = ' - '.join([_("CNPJ: %s") % company.cnpj,
                               _("State Registry: %s") % company.state_registry])
        self.assertEquals(data['lines'], [address, contact, register])
