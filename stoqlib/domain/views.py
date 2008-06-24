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

from stoqlib.domain.commission import CommissionSource
from stoqlib.domain.interfaces import ISellable
from stoqlib.domain.product import (Product, ProductAdaptToSellable,
                                    ProductAdaptToStorable,
                                    ProductStockItem,
                                    ProductHistory)
from stoqlib.domain.sellable import (ASellable, SellableUnit,
                                     BaseSellableInfo, SellableCategory,
                                     SellableTaxConstant)

class ProductFullStockView(Viewable):
    """Stores information about products.
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
        product_id=Product.q.id,
        tax_description=SellableTaxConstant.q.description,
        category_description=SellableCategory.q.description,
        stock=func.SUM(ProductStockItem.q.quantity +
                       ProductStockItem.q.logic_quantity),
        )

    joins = [
        # Tax Constant
        LEFTJOINOn(None, SellableTaxConstant,
                   SellableTaxConstant.q.id == ASellable.q.tax_constantID),
        # Category
        LEFTJOINOn(None, SellableCategory,
                   SellableCategory.q.id == ASellable.q.categoryID),
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

    def get_unit_description(self):
        unit = ISellable(self.product).get_unit_description()
        if unit == u"":
            return u"un"
        return unit

    def get_product_and_category_description(self):
        """Returns the product and the category description in one string.
        The category description will be formatted inside square
        brackets, if any. Otherwise, only the product description will
        be returned.
        """
        category_description = ''
        if self.category_description:
            category_description += '[' + self.category_description + '] '

        return category_description + self.description

    @property
    def product(self):
        return Product.get(self.product_id, connection=self.get_connection())


class ProductWithStockView(ProductFullStockView):
    """Stores information about products, since product has a purchase or sale.
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

    columns = ProductFullStockView.columns
    clause = AND(
        ProductFullStockView.clause,
        ProductStockItem.q.quantity >= 0,
        ProductStockItem.q.logic_quantity >= 0,
        )
    ProductFullStockView.joins


class ProductQuantityView(Viewable):
    """Stores information about products solded and received.

    @cvar id: the id of the sellable_id of products_quantity table
    @cvar description: the product description
    @cvar branch_id: the id of person_adapt_to_branch table
    @cvar quantity_sold: the quantity solded of product
    @cvar quantity_transfered: the quantity transfered of product
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
        quantity_transfered=func.SUM(ProductHistory.q.quantity_transfered),
        quantity_retained=func.SUM(ProductHistory.q.quantity_retained),
        )

    hidden_columns = ['sold_date', 'received_date']

    joins = [
        INNERJOINOn(None, ASellable,
                    ProductHistory.q.sellableID == ASellable.q.id),
        INNERJOINOn(None, BaseSellableInfo,
                    ASellable.q.base_sellable_infoID == BaseSellableInfo.q.id),
    ]


class SellableFullStockView(Viewable):
    """Stores information about products.
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
