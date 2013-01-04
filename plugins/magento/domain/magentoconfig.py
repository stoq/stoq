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
                                  BoolCol, Reference)
from stoqlib.database.runtime import get_current_branch, new_store
from stoqlib.domain.base import Domain
from stoqlib.domain.person import Employee, Individual, Person, SalesPerson
from stoqlib.domain.sellable import Sellable, SellableCategory
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

    __storm_table__ = 'magento_config'

    url = UnicodeCol()
    api_user = UnicodeCol(default='')
    api_key = UnicodeCol(default='')

    tz_hours = DecimalCol(default=decimal.Decimal(0))
    qty_days_as_new = IntCol(default=45)
    branch_id = IntCol()
    branch = Reference(branch_id, 'Branch.id')
    salesperson_id = IntCol()
    salesperson = Reference(salesperson_id, 'SalesPerson.id')

    default_product_set = IntCol(default=None)
    root_category = IntCol(default=None)

    def __init__(self, store=None, **kwargs):
        if not 'salesperson' in kwargs:
            kwargs['salesperson'] = self._create_salesperson()
        if not 'branch' in kwargs:
            kwargs['branch'] = get_current_branch(store)

        super(MagentoConfig, self).__init__(store=store, **kwargs)

    #
    #  Public API
    #

    def get_table_config(self, klass):
        store = self.store
        name = klass.__name__
        table_config = store.find(MagentoTableConfig, config=self,
                                  magento_table=name).one()
        if not table_config:
            store = new_store()
            MagentoTableConfig(store=store,
                               config=store.fetch(self),
                               magento_table=name)
            store.commit(close=True)
            # We created the obj. Now the find().one() above will work
            return self.get_table_config(klass)

        return table_config

    #
    #  AbstractDomain hooks
    #

    def on_create(self):
        from magentoproduct import MagentoProduct, MagentoCategory
        store = self.store
        sysparam_ = sysparam(store)

        # When commiting, ensure we known all products to synchronize using the
        # server registered on self. Events should take care of creating others
        for sellable in Sellable.select(store=store):
            if sellable.service == sysparam_.DELIVERY_SERVICE:
                # Do not sync delivery service
                continue

            # Just need to create. All other information will be synchronized
            # on MagentoProduct.synchronize
            mag_product = MagentoProduct(store=store,
                                         sellable=sellable,
                                         config=self)
            assert mag_product
        # Like products above, ensure we know all categories to synchronize.
        for category in SellableCategory.select(store=store):
            mag_category = MagentoCategory(store=store,
                                           category=category,
                                           config=self)
            assert mag_category

    #
    #  Private
    #

    def _create_salesperson(self):
        store = self.store
        old_magento_configs = MagentoConfig.select(store=store)
        if len(list(old_magento_configs)):
            # Try to reuse the salesperson of the already existing
            # MagentoConfig. Probably it's the one we create bellow
            return old_magento_configs[0].salesperson

        sysparam_ = sysparam(store)
        name = _("Magento e-commerce")
        occupation = _("E-commerce software")
        role = sysparam_.DEFAULT_SALESPERSON_ROLE

        person = Person(store=store,
                        name=name)
        Individual(person=person,
                   occupation=occupation,
                   store=store)
        Employee(person=person,
                 role=role,
                 store=store)

        return SalesPerson(person=person, store=store)


class MagentoTableConfig(Domain):
    """Responsible for storing specific configurations for classes

    @ivar config: the :class:`MagentoConfig` associated with this obj
    @ivar magento_table: the name of the table associated with this config
    """

    __storm_table__ = 'magento_table_config'

    config_id = IntCol()
    config = Reference(config_id, 'MagentoConfig.id')
    magento_table = UnicodeCol()
    last_sync_date = DateTimeCol(default=datetime.datetime.min)
    need_ensure_config = BoolCol(default=True)
