# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2013 Async Open Source
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU Lesser General Public License
## as published by the Free Software Foundation; either version 2
## of the License, or (at your option) any later version.
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
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

""" Useful functions related to reports building and visualization. """

import base64
import logging
import platform

from kiwi.environ import environ

from stoqlib.database.runtime import get_current_branch, get_default_store
from stoqlib.exceptions import DatabaseInconsistency
from stoqlib.lib.formatters import format_phone_number
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext
_system = platform.system()
log = logging.getLogger(__name__)
# a list of programs to be tried when a report needs be viewed


def get_logo_data(store):
    logo_domain = sysparam.get_object(store, 'CUSTOM_LOGO_FOR_REPORTS')
    if logo_domain and logo_domain.image:
        data = logo_domain.image
    else:
        data = environ.get_resource_string('stoq', 'pixmaps', 'stoq_logo_bgwhite.png')

    return 'data:image/png;base64,' + base64.b64encode(data)


def get_header_data():
    default_store = get_default_store()

    branch = get_current_branch(default_store)
    person = branch.person
    company = person.company
    main_address = person.get_main_address()

    if not person.name:  # pragma nocover
        raise DatabaseInconsistency("The person by ID %r should have a "
                                    "name at this point" % (person.id, ))

    data = {
        'title': branch.get_description(),
        'lines': [],
    }

    # Address
    if main_address:
        address_parts = []
        address_parts.append(main_address.get_address_string())
        if main_address.postal_code:
            address_parts.append(main_address.postal_code)
        if main_address.get_city():
            address_parts.append(main_address.get_city())
        if main_address.get_state():
            address_parts.append(main_address.get_state())
        if address_parts:
            data['lines'].append(' - '.join(address_parts))

    # Contact
    contact_parts = []
    if person.phone_number:
        contact_parts.append(format_phone_number(person.phone_number))
    if person.mobile_number:
        contact_parts.append(format_phone_number(person.mobile_number))
    if person.fax_number:
        contact_parts.append(_("Fax: %s") %
                             format_phone_number(person.fax_number))
    if person.email:
        contact_parts.append(person.email)
    if contact_parts:
        data['lines'].append(' - '.join(contact_parts))

    # Company details
    if company:
        company_parts = []
        if company.get_cnpj_number():
            company_parts.append(_("CNPJ: %s") % company.cnpj)
        if company.get_state_registry_number():
            company_parts.append(_("State Registry: %s") %
                                 company.state_registry)

        if company_parts:
            data['lines'].append(' - '.join(company_parts))

    return data
