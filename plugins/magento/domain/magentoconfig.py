# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2011 Async Open Source <http://www.async.com.br>
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
## GNU General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

import datetime
import decimal

from kiwi.component import get_utility, provide_utility
from zope.interface import implements

from stoqlib.database.orm import (DecimalCol, IntCol, UnicodeCol, DateTimeCol,
                                  ForeignKey)
from stoqlib.database.runtime import get_connection
from stoqlib.domain.base import Domain
from stoqlib.domain.interfaces import ISalesPerson, IEmployee, IIndividual
from stoqlib.domain.person import Person
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext

from magentointerfaces import IMagentoConfig

_ = stoqlib_gettext


def get_config(trans=None):
    """Returns a singleton of MagentoConfig

    @param trans: if given, the config will be retrieved to this
        transaction before returning.
    """
    config = get_utility(IMagentoConfig, None)

    if not config:
        config = MagentoConfig.selectOne(connection=get_connection())
        assert config
        provide_utility(IMagentoConfig, config)
        assert get_utility(IMagentoConfig, None)

    if trans:
        return trans.get(config)

    return config


class MagentoConfig(Domain):
    """Class for storing Magento config information

    @ivar url: the path to magento xmlrpc api
    @ivar api_user: the api user set in magento configuration
    @ivar api_key: the api_user's key
    @ivar tz_hours: the timezone difference, in hours, e.g. -3 for GMT-3
    @ivar qty_days_as_new: how many days to set a product as new on magento
    @ivar branch: the branch which will be used to query stock information
    """

    implements(IMagentoConfig)

    url = UnicodeCol()
    api_user = UnicodeCol(default='')
    api_key = UnicodeCol(default='')

    tz_hours = DecimalCol(default=decimal.Decimal(0))
    qty_days_as_new = IntCol(default=45)
    branch = ForeignKey('PersonAdaptToBranch')
    salesperson = ForeignKey('PersonAdaptToSalesPerson')

    #
    #  Public API
    #

    def get_table_config(self, klass):
        """Returns the magento config specific to C{klass}

        @returns: the L{MagentoTableConfig} associated with C{klass}
        """
        conn = self.get_connection()
        table = klass.__name__

        table_config = MagentoTableConfig.selectOneBy(connection=conn,
                                                      magento_table=table)
        if not table_config:
            table_config = MagentoTableConfig(connection=conn,
                                              magento_table=table)

        return table_config

    #
    #  ORMObject hooks
    #

    def _create(self, *args, **kwargs):
        if not 'salesperson' in kwargs:
            kwargs['salesperson'] = self._create_salesperson()

        super(MagentoConfig, self)._create(*args, **kwargs)

    #
    #  Private API
    #

    def _create_salesperson(self):
        conn = self.get_connection()
        sysparam_ = sysparam(conn)
        name = _("Magento e-commerce")
        occupation = _("E-commerce software")
        role = sysparam_.DEFAULT_SALESPERSON_ROLE

        person = Person(connection=conn,
                        name=name)
        person.addFacet(IIndividual,
                        occupation=occupation,
                        connection=conn)
        person.addFacet(IEmployee,
                        role=role,
                        connection=conn)

        return person.addFacet(ISalesPerson, connection=conn)


class MagentoTableConfig(Domain):
    """Class for storing Magento config specific to a C{magento_table}

    @ivar magento_table: the table associated with this config
    @ivar last_sync_date: the last date, on Magento, that C{magento_table}
        was successfully synchronized for the last time
    """

    magento_table = UnicodeCol()
    last_sync_date = DateTimeCol(default=datetime.datetime.min)
