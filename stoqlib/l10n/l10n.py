# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012 Async Open Source
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
##

from kiwi.python import namedAny

from stoqlib.l10n.generic import generic

# FIXME: When fixing bug 5100, this won't be necessary anymore.
# This maps country lists in stoqlib.lib.countries to ISO 639-1
iso639_list = {
    # FIXME: We should use a combo in parameters instead.
    'brazil': 'br',
    'brasil': 'br',
    'sverige': 'sv',
    'sweden': 'sv',
}


def get_l10n_module(country=None):
    if not country:
        from stoqlib.lib.parameters import sysparam
        country = sysparam.get_string('COUNTRY_SUGGESTED')

    short = iso639_list.get(country.lower(), None)
    if short is None:
        return generic

    path = 'stoqlib.l10n.%s.%s' % (short, short)
    try:
        module = namedAny(path)
    except (ImportError, AttributeError):
        return generic

    return module


def get_l10n_field(field_name, country=None):
    module = get_l10n_module(country)
    field = getattr(module, field_name, None)
    if field is None:
        assert hasattr(generic, field_name)
        field = getattr(generic, field_name)
    return field
