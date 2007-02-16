# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2007 Async Open Source <http://www.async.com.br>
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
## Author(s):   Johan Dahlin <jdahlin@async.com.br>
##

from sqlobject.viewable import Viewable
from stoqlib.domain.person import Person, PersonAdaptToSupplier
from stoqlib.domain.product import (Product, ProductAdaptToSellable,
                                    ProductAdaptToStorable,
                                    ProductStockItem,
                                    ProductSupplierInfo)
from stoqlib.domain.sellable import ASellable, SellableUnit, BaseSellableInfo
from stoqlib.domain.stock import AbstractStockItem
from sqlobject.sqlbuilder import func, AND, INNERJOINOn, LEFTJOINOn

class WarehouseView(Viewable):

    columns = dict(
        id=ASellable.q.id,
        code=ASellable.q.code,
        barcode=ASellable.q.barcode,
        status=ASellable.q.status,
        cost=ASellable.q.cost,
        price=BaseSellableInfo.q.price,
        is_valid_model=BaseSellableInfo.q._is_valid_model,
        description=BaseSellableInfo.q.description,
        unit=SellableUnit.q.description,
        product_id=Product.q.id,
        supplier_name=Person.q.name,
        stock=func.SUM(AbstractStockItem.q.quantity +
                       AbstractStockItem.q.logic_quantity),
        )

    joins = [
        # Sellable unit
        LEFTJOINOn(None, SellableUnit,
                    SellableUnit.q.id == ASellable.q.unitID),
        # Product
        INNERJOINOn(None, ProductAdaptToSellable,
                    ProductAdaptToSellable.q.id == ASellable.q.id),
        INNERJOINOn(None, Product,
                    Product.q.id == ProductAdaptToSellable.q._originalID),
        # Product Stock Item
        INNERJOINOn(None, ProductAdaptToStorable,
                    ProductAdaptToStorable.q._originalID == Product.q.id),
        INNERJOINOn(None, ProductStockItem,
                    ProductStockItem.q.storableID == ProductAdaptToStorable.q.id),
        INNERJOINOn(None, AbstractStockItem,
                    AbstractStockItem.q.id == ProductStockItem.q.id),
        # Product Supplier
        INNERJOINOn(None, ProductSupplierInfo,
                    AND(ProductSupplierInfo.q.productID == Product.q.id,
                        ProductSupplierInfo.q.is_main_supplier == True)),
        INNERJOINOn(None, PersonAdaptToSupplier,
                    PersonAdaptToSupplier.q.id == ProductSupplierInfo.q.supplierID),
        INNERJOINOn(None, Person,
                    Person.q.id == PersonAdaptToSupplier.q._originalID),
        ]

    clause = AND(
        BaseSellableInfo.q.id == ASellable.q.base_sellable_infoID,
        BaseSellableInfo.q._is_valid_model == True,
        )

    @classmethod
    def select_by_branch(cls, query, branch, connection=None):
        if branch:
            branch_query = AbstractStockItem.q.branchID == branch.id
            if query:
                query = AND(query, branch_query)
            else:
                query = branch_query

        return cls.select(query, connection=connection)
