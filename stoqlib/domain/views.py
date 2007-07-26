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
##              Fabio Morbec <fabio@async.com.br>
##

from sqlobject.viewable import Viewable
from sqlobject.sqlbuilder import func, AND, INNERJOINOn, LEFTJOINOn, OR

from stoqlib.domain.commissions import Commission, CommissionSource
from stoqlib.domain.person import Person, PersonAdaptToSalesPerson
from stoqlib.domain.product import (Product, ProductAdaptToSellable,
                                    ProductAdaptToStorable,
                                    ProductStockItem,
                                    ProductHistory)
from stoqlib.domain.sale import Sale, SaleItem
from stoqlib.domain.sellable import (ASellable, SellableUnit,
                                     BaseSellableInfo, SellableCategory)

class ProductFullStockView(Viewable):
    """
    Stores information about products.
    This view is used to query stock information on a certain branch.

    @cvar id: the id of the asellable table
    @cvar barcode: the sellable barcode
    @cvar status: the sellable status
    @cvar cost: the sellable cost
    @cvar price: the sellable price
    @cvar description: the sellable description
    @cvar unit: the unit of the product
    @cvar product_id: the id of the product table
    @cvar branch_id: the id of person_adapt_to_branch table
    @cvar stock: the stock of the product
     """

    columns = dict(
        id=ASellable.q.id,
        barcode=ASellable.q.barcode,
        status=ASellable.q.status,
        cost=ASellable.q.cost,
        price=BaseSellableInfo.q.price,
        description=BaseSellableInfo.q.description,
        unit=SellableUnit.q.description,
        product_id=Product.q.id,
        stock=func.SUM(ProductStockItem.q.quantity +
                       ProductStockItem.q.logic_quantity),
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
        LEFTJOINOn(None, ProductAdaptToStorable,
                   ProductAdaptToStorable.q._originalID == Product.q.id),
        LEFTJOINOn(None, ProductStockItem,
                   ProductStockItem.q.storableID ==
                   ProductAdaptToStorable.q.id),
        ]

    clause = AND(
        BaseSellableInfo.q.id == ASellable.q.base_sellable_infoID,
        )

    @classmethod
    def select_by_branch(cls, query, branch, connection=None):
        if branch:
            branch_query = ProductStockItem.q.branchID == branch.id
            if query:
                query = AND(query, branch_query)
            else:
                query = branch_query

        return cls.select(query, connection=connection)

    @property
    def product(self):
        return Product.get(self.product_id, connection=self.get_connection())


class ProductQuantityView(Viewable):
    """
    Stores information about products solded and received.

    @cvar id: the id of the sellable_id of products_quantity table
    @cvar description: the product description
    @cvar branch_id: the id of person_adapt_to_branch table
    @cvar quantity_sold: the quantity solded of product
    @cvar quantity_received: the quantity received of product
    @cvar branch: the id of the branch_id of producst_quantity table
    @cvar date_sale: the date of product's sale
    @cvar date_received: the date of product's received
     """

    columns = dict(
        id=ProductHistory.q.sellableID,
        description=BaseSellableInfo.q.description,
        branch=ProductHistory.q.branchID,
        sold_date=ProductHistory.q.sold_date,
        received_date=ProductHistory.q.received_date,
        quantity_sold=func.SUM(ProductHistory.q.quantity_sold),
        quantity_received=func.SUM(ProductHistory.q.quantity_received),
        )

    hidden_columns = ['sold_date', 'received_date']

    joins = [
        INNERJOINOn(None, ASellable,
                    ProductHistory.q.sellableID == ASellable.q.id),
        INNERJOINOn(None, BaseSellableInfo,
                    ASellable.q.base_sellable_infoID == BaseSellableInfo.q.id)
    ]

class SellableFullStockView(Viewable):
    """
    Stores information about products.
    This view is used to query stock information on a certain branch.

    @cvar id: the id of the asellable table
    @cvar barcode: the sellable barcode
    @cvar status: the sellable status
    @cvar cost: the sellable cost
    @cvar price: the sellable price
    @cvar description: the sellable description
    @cvar unit: the unit of the product or None
    @cvar product_id: the id of the product table or None
    @cvar branch_id: the id of person_adapt_to_branch table or None
    @cvar stock: the stock of the product or None
     """

    columns = dict(
        id=ASellable.q.id,
        barcode=ASellable.q.barcode,
        status=ASellable.q.status,
        cost=ASellable.q.cost,
        price=BaseSellableInfo.q.price,
        description=BaseSellableInfo.q.description,
        unit=SellableUnit.q.description,
        product_id=Product.q.id,
        stock=func.SUM(ProductStockItem.q.quantity +
                       ProductStockItem.q.logic_quantity),
        )

    joins = [
        # Sellable unit
        LEFTJOINOn(None, SellableUnit,
                   SellableUnit.q.id == ASellable.q.unitID),
        # Product
        LEFTJOINOn(None, ProductAdaptToSellable,
                   ProductAdaptToSellable.q.id == ASellable.q.id),
        LEFTJOINOn(None, Product,
                   Product.q.id == ProductAdaptToSellable.q._originalID),
        # Product Stock Item
        LEFTJOINOn(None, ProductAdaptToStorable,
                   ProductAdaptToStorable.q._originalID == Product.q.id),
        LEFTJOINOn(None, ProductStockItem,
                   ProductStockItem.q.storableID ==
                   ProductAdaptToStorable.q.id),
        ]

    clause = AND(
        BaseSellableInfo.q.id == ASellable.q.base_sellable_infoID,
        )

    @classmethod
    def select_by_branch(cls, query, branch, connection=None):
        if branch:
            # We need the OR part to be able to list services and gift certificates
            branch_query = OR(ProductStockItem.q.branchID == branch.id,
                              ProductStockItem.q.branchID == None)
            if query:
                query = AND(query, branch_query)
            else:
                query = branch_query

        return cls.select(query, connection=connection)

class SellableCategoryView(Viewable):
    """Stores information about categories.
       This view is used to query the category with the related
        commission source.
    """

    columns = dict(
        id=SellableCategory.q.id,
        commission=CommissionSource.q.direct_value,
        installments_commission=CommissionSource.q.installments_value,
        category_id=SellableCategory.q.id,
        description=SellableCategory.q.description,
        suggested_markup=SellableCategory.q.suggested_markup,
    )

    joins = [
        # commission source
        LEFTJOINOn(None, CommissionSource,
                   CommissionSource.q.categoryID ==
                   SellableCategory.q.id),
       ]

    @property
    def category(self):
        return SellableCategory.get(self.category_id,
                                    connection=self.get_connection())

    def get_commission(self):
        if self.commission:
            return self.commission

        source = self._get_base_source_commission()
        if source:
            return source.direct_value

    def get_installments_commission(self):
        if self.commission:
            return self.installments_commission

        source = self._get_base_source_commission()
        if source:
            return source.installments_value

    def _get_base_source_commission(self):
        base_category = self.category.category
        if not base_category:
            return

        return CommissionSource.selectOneBy(category=base_category,
                                            connection=self.get_connection())

class CommissionView(Viewable):

    columns = dict(
        id=Sale.q.id,
        commission_value=Commission.q.value,
        commission_percentage=Commission.q.value/Sale.q.total_amount*100,
        salesperson_name=Person.q.name,
        total_quantity= func.SUM(SaleItem.q.quantity),
        total_amount=Sale.q.total_amount,
        open_date=Sale.q.open_date,
       )

    joins = [
        # commission
        INNERJOINOn(None, Commission,
            Commission.q.saleID == Sale.q.id),

        # person
        INNERJOINOn(None, PersonAdaptToSalesPerson,
            PersonAdaptToSalesPerson.q.id == Commission.q.salespersonID),

        INNERJOINOn(None, Person,
            Person.q.id == PersonAdaptToSalesPerson.q._originalID),

        # sale item
        LEFTJOINOn(None, SaleItem,
            SaleItem.q.saleID == Commission.q.saleID),
        ]
