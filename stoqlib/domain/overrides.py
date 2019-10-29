# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

#
# Copyright (C) 2018 Async Open Source <http://www.async.com.br>
# All rights reserved
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., or visit: http://www.gnu.org/.
#
# Author(s): Stoq Team <stoq-devel@async.com.br>
#

from storm.references import Reference

from stoqlib.database.properties import (BoolCol, DateTimeCol, EnumCol,
                                         IdCol, PercentCol, QuantityCol,
                                         PriceCol, UnicodeCol)
from stoqlib.domain.base import Domain
from stoqlib.domain.person import Branch


class SellableBranchOverride(Domain):
    __storm_table__ = 'sellable_branch_override'

    status = EnumCol()

    base_price = PriceCol()

    price_last_updated = DateTimeCol()

    max_discount = PercentCol()

    tax_constant_id = IdCol()
    tax_constant = Reference(tax_constant_id, 'SellableTaxConstant.id')

    default_sale_cfop_id = IdCol()
    default_sale_cfop = Reference(default_sale_cfop_id, 'CfopData.id')

    on_sale_price = PriceCol()
    on_sale_start_date = DateTimeCol()
    on_sale_end_date = DateTimeCol()

    branch_id = IdCol()
    branch = Reference(branch_id, 'Branch.id')

    sellable_id = IdCol()
    sellable = Reference(sellable_id, 'Sellable.id')

    #: specifies whether the product requires kitchen production
    requires_kitchen_production = BoolCol()

    @classmethod
    def find_by_sellable(cls, sellable, branch):
        return sellable.store.find(cls, sellable=sellable, branch=branch).one()


class ProductBranchOverride(Domain):
    __storm_table__ = 'product_branch_override'

    location = UnicodeCol()

    icms_template_id = IdCol()
    icms_template = Reference(icms_template_id, 'ProductIcmsTemplate.id')

    ipi_template_id = IdCol()
    ipi_template = Reference(ipi_template_id, 'ProductIpiTemplate.id')

    pis_template_id = IdCol()
    pis_template = Reference(pis_template_id, 'ProductPisTemplate.id')

    cofins_template_id = IdCol()
    cofins_template = Reference(cofins_template_id, 'ProductCofinsTemplate.id')

    branch_id = IdCol()
    branch = Reference(branch_id, 'Branch.id')

    product_id = IdCol()
    product = Reference(product_id, 'Product.id')

    #: Brazil specific. NFE. Código Benefício Fiscal
    c_benef = UnicodeCol(default=None)

    @classmethod
    def find_product(cls, branch: Branch, product):
        return product.store.find(cls, product=product, branch=branch).one()


class StorableBranchOverride(Domain):
    __storm_table__ = 'storable_branch_override'

    minimum_quantity = QuantityCol()
    maximum_quantity = QuantityCol()

    branch_id = IdCol()
    branch = Reference(branch_id, 'Branch.id')

    storable_id = IdCol()
    storable = Reference(storable_id, 'Storable.id')


class ServiceBranchOverride(Domain):
    __storm_table__ = 'service_branch_override'

    city_taxation_code = UnicodeCol()
    service_list_item_code = UnicodeCol()
    p_iss = PercentCol()

    branch_id = IdCol()
    branch = Reference(branch_id, 'Branch.id')

    service_id = IdCol()
    service = Reference(service_id, 'Service.id')
