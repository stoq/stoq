# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2008 Async Open Source <http://www.async.com.br>
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

"""Bootstrapping the GUI parts of Stoq
"""

from kiwi.component import provide_utility
from kiwi.datatypes import get_localeconv
from kiwi.ui.widgets.label import ProxyLabel


def _register_proxy_markup():
    ProxyLabel.replace('$CURRENCY', get_localeconv()['currency_symbol'])


def _register_domain_slave_mapper():
    from stoqlib.gui.interfaces import IDomainSlaveMapper
    from stoqlib.gui.domainslavemapper import DefaultDomainSlaveMapper
    provide_utility(IDomainSlaveMapper, DefaultDomainSlaveMapper(),
                    replace=True)


def bootstrap():
    """Run the UI bootstrap for Stoqlib,
    this should only happen once.
    """
    _register_proxy_markup()
    _register_domain_slave_mapper()
