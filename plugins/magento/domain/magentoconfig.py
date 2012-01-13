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

from stoqlib.database.orm import (DecimalCol, IntCol, UnicodeCol, DateTimeCol,
                                  BoolCol, ForeignKey)
from stoqlib.database.runtime import get_current_branch, new_transaction
from stoqlib.domain.base import Domain
from stoqlib.domain.interfaces import ISalesPerson, IEmployee, IIndividual
from stoqlib.domain.person import Person
from stoqlib.domain.product import Product
from stoqlib.domain.sellable import SellableCategory
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class MagentoConfig(Domain):
    """Class for storing Magento config information

    @ivar url: the path to magento xmlrpc api
    @ivar api_user: the api user set in magento configuration
    @ivar api_key: the api_user's key
    @ivar tz_hours: the timezone difference, in hours, e.g. -3 for GMT-3
    @ivar qty_days_as_new: how many days to set a product as new on magento
    @ivar branch: the branch which will be used to query stock information
    @ivar salesperson: the magento sales salesperson
    @ivar default_product_set: the id of the default products set on magento
    @ivar root_category: the id of the root category on magento
    """

    url = UnicodeCol()
    api_user = UnicodeCol(default='')
    api_key = UnicodeCol(default='')

    tz_hours = DecimalCol(default=decimal.Decimal(0))
    qty_days_as_new = IntCol(default=45)
    branch = ForeignKey('PersonAdaptToBranch')
    salesperson = ForeignKey('PersonAdaptToSalesPerson')

    default_product_set = IntCol(default=None)
    root_category = IntCol(default=None)

    #
    #  Public API
    #

    def get_table_config(self, klass):
        conn = self.get_connection()
        name = klass.__name__
        table_config = MagentoTableConfig.selectOneBy(connection=conn,
                                                      config=self,
                                                      magento_table=name)
        if not table_config:
            trans = new_transaction()
            MagentoTableConfig(connection=trans,
                               config=self,
                               magento_table=name)
            trans.commit(close=True)
            # We created the obj. Now the selectOneBy above will work
            return self.get_table_config(klass)

        return table_config

    #
    #  ORMObject hooks
    #

    def _create(self, *args, **kwargs):
        conn = self.get_connection()
        if not 'salesperson' in kwargs:
            kwargs['salesperson'] = self._create_salesperson()
        if not 'branch' in kwargs:
            kwargs['branch'] = get_current_branch(conn)

        super(MagentoConfig, self)._create(*args, **kwargs)

    #
    #  AbstractDomain hooks
    #

    def on_create(self):
        from magentoproduct import MagentoProduct, MagentoCategory
        conn = self.get_connection()

        # When commiting, ensure we known all products to synchronize using the
        # server registered on self. Events should take care of creating others
        for product in Product.select(connection=conn):
            # Just need to create. All other information will be synchronized
            # on MagentoProduct.synchronize
            mag_product = MagentoProduct(connection=conn,
                                         product=product,
                                         config=self)
            assert mag_product
        # Like products above, ensure we know all categories to synchronize.
        for category in SellableCategory.select(connection=conn):
            mag_category = MagentoCategory(connection=conn,
                                           category=category,
                                           config=self)
            assert mag_category

    #
    #  Private
    #

    def _create_salesperson(self):
        conn = self.get_connection()
        old_magento_configs = MagentoConfig.select(connection=conn)
        if len(list(old_magento_configs)):
            # Try to reuse the salesperson of the already existing
            # MagentoConfig. Probably it's the one we create bellow
            return old_magento_configs[0].salesperson

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
    """Responsible for storing specific configurations for classes

    @ivar config: the L{MagentoConfig} associated with this obj
    @ivar magento_table: the name of the table associated with this config
    """

    config = ForeignKey('MagentoConfig')
    magento_table = UnicodeCol()
    last_sync_date = DateTimeCol(default=datetime.datetime.min)
    need_ensure_config = BoolCol(default=True)
