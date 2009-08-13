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

from stoqlib.database.orm import const, AND, INNERJOINOn, LEFTJOINOn, OR
from stoqlib.database.orm import Viewable, Field, Alias
from stoqlib.database.runtime import get_connection
from stoqlib.domain.commission import CommissionSource
from stoqlib.domain.person import (Person, PersonAdaptToSupplier,
                                   PersonAdaptToUser)
from stoqlib.domain.product import (Product,
                                    ProductAdaptToStorable,
                                    ProductStockItem,
                                    ProductHistory,
                                    ProductComponent)
from stoqlib.domain.purchase import (Quotation, QuoteGroup, PurchaseOrder,
                                     PurchaseItem)
from stoqlib.domain.receiving import ReceivingOrderItem, ReceivingOrder
from stoqlib.domain.sellable import (Sellable, SellableUnit,
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
    @cvar location: the location of the product
    @cvar branch_id: the id of person_adapt_to_branch table
    @cvar stock: the stock of the product
     """

    columns = dict(
        id=Sellable.q.id,
        code=Sellable.q.code,
        barcode=Sellable.q.barcode,
        status=Sellable.q.status,
        cost=Sellable.q.cost,
        price=BaseSellableInfo.q.price,
        description=BaseSellableInfo.q.description,
        product_id=Product.q.id,
        location=Product.q.location,
        tax_description=SellableTaxConstant.q.description,
        category_description=SellableCategory.q.description,
        stock=const.SUM(ProductStockItem.q.quantity +
                        ProductStockItem.q.logic_quantity),
        )

    joins = [
        # Tax Constant
        LEFTJOINOn(None, SellableTaxConstant,
                   SellableTaxConstant.q.id == Sellable.q.tax_constantID),
        # Category
        LEFTJOINOn(None, SellableCategory,
                   SellableCategory.q.id == Sellable.q.categoryID),
        # Product
        INNERJOINOn(None, Product,
                    Product.q.sellableID == Sellable.q.id),
        # Product Stock Item
        LEFTJOINOn(None, ProductAdaptToStorable,
                   ProductAdaptToStorable.q._originalID == Product.q.id),
        LEFTJOINOn(None, ProductStockItem,
                   ProductStockItem.q.storableID ==
                   ProductAdaptToStorable.q.id),
        ]

    clause = AND(
        BaseSellableInfo.q.id == Sellable.q.base_sellable_infoID,
        )

    @classmethod
    def select_by_branch(cls, query, branch, having=None, connection=None):
        if branch:
            # Also show products that were never purchased.
            branch_query = OR(ProductStockItem.q.branchID == branch.id,
                              ProductStockItem.q.branchID == None)
            if query:
                query = AND(query, branch_query)
            else:
                query = branch_query

        return cls.select(query, having=having, connection=connection)

    def get_unit_description(self):
        unit = self.product.sellable.get_unit_description()
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


class ProductComponentView(ProductFullStockView):
    columns = ProductFullStockView.columns
    clause = AND(ProductFullStockView.clause,
                 ProductComponent.q.productID == Product.q.id,)

    @property
    def sellable(self):
        return Sellable.get(self.id, connection=self.get_connection())


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


class _PurchaseItemTotal(Viewable):
    columns = dict(
        id=PurchaseItem.q.sellableID,
        to_receive=const.SUM(PurchaseItem.q.quantity-
                             PurchaseItem.q.quantity_received)
    )

    joins = []


class ProductFullStockItemView(ProductFullStockView):
    # ProductFullStockView already joins with a 1 to Many table (Sellable
    # with ProductStockItem).
    #
    # This is why we must join PurchaseItem (another 1 to many table) in a
    # subquery

    _purchase_total = "(%s) AS _purchase_total" % str(
                    _PurchaseItemTotal.select(connection=get_connection()))

    columns = ProductFullStockView.columns.copy()
    columns.update(dict(
        minimum_quantity=ProductAdaptToStorable.q.minimum_quantity,
        maximum_quantity=ProductAdaptToStorable.q.maximum_quantity,
        to_receive_quantity=Field('_purchase_total', 'to_receive'),
        difference=(const.SUM(
            ProductStockItem.q.quantity + ProductStockItem.q.logic_quantity) -
            ProductAdaptToStorable.q.minimum_quantity)))

    joins = ProductFullStockView.joins[:]
    joins.append(LEFTJOINOn(None, _purchase_total,
                            Field('_purchase_total', 'id') == Sellable.q.id))


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
        code=Sellable.q.code,
        description=BaseSellableInfo.q.description,
        branch=ProductHistory.q.branchID,
        sold_date=ProductHistory.q.sold_date,
        received_date=ProductHistory.q.received_date,
        quantity_sold=const.SUM(ProductHistory.q.quantity_sold),
        quantity_received=const.SUM(ProductHistory.q.quantity_received),
        quantity_transfered=const.SUM(ProductHistory.q.quantity_transfered),
        quantity_retained=const.SUM(ProductHistory.q.quantity_retained),
        )

    hidden_columns = ['sold_date', 'received_date']

    joins = [
        INNERJOINOn(None, Sellable,
                    ProductHistory.q.sellableID == Sellable.q.id),
        INNERJOINOn(None, BaseSellableInfo,
                    Sellable.q.base_sellable_infoID == BaseSellableInfo.q.id),
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
        id=Sellable.q.id,
        code=Sellable.q.code,
        barcode=Sellable.q.barcode,
        status=Sellable.q.status,
        cost=Sellable.q.cost,
        price=BaseSellableInfo.q.price,
        description=BaseSellableInfo.q.description,
        unit=SellableUnit.q.description,
        product_id=Product.q.id,
        stock=const.SUM(ProductStockItem.q.quantity +
                       ProductStockItem.q.logic_quantity),
        )

    joins = [
        # Sellable unit
        LEFTJOINOn(None, SellableUnit,
                   SellableUnit.q.id == Sellable.q.unitID),
        # Product
        LEFTJOINOn(None, Product,
                   Product.q.sellableID == Sellable.q.id),
        # Product Stock Item
        LEFTJOINOn(None, ProductAdaptToStorable,
                   ProductAdaptToStorable.q._originalID == Product.q.id),
        LEFTJOINOn(None, ProductStockItem,
                   ProductStockItem.q.storableID ==
                   ProductAdaptToStorable.q.id),
        ]

    clause = AND(
        BaseSellableInfo.q.id == Sellable.q.base_sellable_infoID,
        )

    @classmethod
    def select_by_branch(cls, query, branch, having=None, connection=None):
        if branch:
            # We need the OR part to be able to list services
            branch_query = OR(ProductStockItem.q.branchID == branch.id,
                              ProductStockItem.q.branchID == None)
            if query:
                query = AND(query, branch_query)
            else:
                query = branch_query

        return cls.select(query, having=having, connection=connection)

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


class QuotationView(Viewable):
    """Stores information about the quote group and its quotes.
    """
    columns = dict(
        id=Quotation.q.id,
        purchase_id=Quotation.q.purchaseID,
        group_id=Quotation.q.groupID,
        group_code=Quotation.q.groupID,
        open_date=PurchaseOrder.q.open_date,
        deadline=PurchaseOrder.q.quote_deadline,
        supplier_name=Person.q.name,
    )

    joins = [
        LEFTJOINOn(None, PurchaseOrder,
                   PurchaseOrder.q.id == Quotation.q.purchaseID),
        LEFTJOINOn(None, PersonAdaptToSupplier,
                   PersonAdaptToSupplier.q.id == PurchaseOrder.q.supplierID),
        LEFTJOINOn(None, Person, Person.q.id ==
                   PersonAdaptToSupplier.q._originalID),
    ]

    clause = AND(QuoteGroup.q.id == Quotation.q.groupID,
                 PurchaseOrder.q._is_valid_model == True)

    @property
    def group(self):
        return QuoteGroup.get(self.group_id, connection=self.get_connection())

    @property
    def quotation(self):
        return Quotation.get(self.id, connection=self.get_connection())

    @property
    def purchase(self):
        return PurchaseOrder.get(self.purchase_id,
                                 connection=self.get_connection())


class PurchasedItemAndStockView(Viewable):
    """Stores information about the purchase items that will be delivered and
    also the quantity that is already in stock.
    This view is used to query which products are going to be delivered and if
    they are on time or not.

    @cvar id: the id of the purchased item
    @cvar product_id: the id of the product
    @cvar purchased: the quantity purchased
    @cvar received: the quantity already received
    @cvar stocked: the quantity in stock
    @cvar expected_receival_date: the date that the item might be deliverd
    @cvar purchase_date: the date when the item was purchased
    @cvar branch: the branch where the purchase was done
    """

    columns = dict(
        id=PurchaseItem.q.id,
        product_id=Product.q.id,
        description=BaseSellableInfo.q.description,
        purchased=PurchaseItem.q.quantity,
        received=PurchaseItem.q.quantity_received,
        stocked=const.SUM(ProductStockItem.q.quantity +
                          ProductStockItem.q.logic_quantity),
        expected_receival_date=PurchaseItem.q.expected_receival_date,
        order_id=PurchaseOrder.q.id,
        purchased_date=PurchaseOrder.q.open_date,
        branch=PurchaseOrder.q.branchID,
    )

    joins = [
        LEFTJOINOn(None, PurchaseItem,
                   PurchaseItem.q.orderID == PurchaseOrder.q.id),
        LEFTJOINOn(None, Sellable,
                    Sellable.q.id == PurchaseItem.q.sellableID),
        INNERJOINOn(None, BaseSellableInfo,
                    Sellable.q.base_sellable_infoID == BaseSellableInfo.q.id),
        LEFTJOINOn(None, Product,
                   Product.q.sellableID == PurchaseItem.q.sellableID),
        LEFTJOINOn(None, ProductAdaptToStorable,
                   ProductAdaptToStorable.q._originalID == Product.q.id),
        LEFTJOINOn(None, ProductStockItem,
                   ProductStockItem.q.storableID == ProductAdaptToStorable.q.id),
    ]

    clause = AND(PurchaseOrder.q.status == PurchaseOrder.ORDER_CONFIRMED,
                 PurchaseOrder.q.branchID == ProductStockItem.q.branchID,
                 PurchaseItem.q.quantity > PurchaseItem.q.quantity_received,)

    @property
    def purchase_item(self):
        return PurchaseItem.get(self.id, connection=self.get_connection())


class PurchaseReceivingView(Viewable):
    """Stores information about received orders.

    @cvar id: the id of the receiving order
    @cvar receival_date: the date when the receiving order was closed
    @cvar invoice_number: the number of the order that was received
    @cvar invoice_total: the total value of the received order
    @cvar purchase_id: the id of the received order
    @cvar branch_id: the id branch where the order was received
    @cvar purchase_responsible_name: the one who have confirmed the purchase
    @cvar responsible_name: the one who has received the order
    @cvar supplier_name: the supplier name
    """
    _Responsible = Alias(Person, "responsible")
    _Supplier = Alias(Person, "supplier")
    _PurchaseUser = Alias(PersonAdaptToUser, "purchase_user")
    _PurchaseResponsible = Alias(Person, "purchase_responsible")

    columns = dict(
        id=ReceivingOrder.q.id,
        receival_date=ReceivingOrder.q.receival_date,
        invoice_number=ReceivingOrder.q.invoice_number,
        invoice_total=ReceivingOrder.q.invoice_total,
        purchase_id=PurchaseOrder.q.id,
        branch_id=ReceivingOrder.q.branchID,
        purchase_responsible_name=_PurchaseResponsible.q.name,
        responsible_name=_Responsible.q.name,
        supplier_name=_Supplier.q.name,
        )

    joins = [
        LEFTJOINOn(None, PurchaseOrder,
                   ReceivingOrder.q.purchaseID == PurchaseOrder.q.id),
        LEFTJOINOn(None, _PurchaseUser,
                   PurchaseOrder.q.responsibleID == _PurchaseUser.q.id),
        LEFTJOINOn(None, _PurchaseResponsible,
                   _PurchaseUser.q._originalID == _PurchaseResponsible.q.id),
        LEFTJOINOn(None, PersonAdaptToSupplier,
                   ReceivingOrder.q.supplierID == PersonAdaptToSupplier.q.id),
        LEFTJOINOn(None, _Supplier,
                   PersonAdaptToSupplier.q._originalID == _Supplier.q.id),
        LEFTJOINOn(None, PersonAdaptToUser,
                   ReceivingOrder.q.responsibleID == PersonAdaptToUser.q.id),
        LEFTJOINOn(None, _Responsible,
                   PersonAdaptToUser.q._originalID == _Responsible.q.id),
    ]


class ReceivingItemView(Viewable):
    """Stores information about receiving items.
    This view is used to query products that are going to be received or was
    already received and the information related to that process.

    @cvar id: the id of the receiving item
    @cvar order_id: the id of the receiving order
    @cvar purchase_id: the id of the purchase order
    @cvar purchase_item_id: the id of the purchase item
    @cvar sellable_id: the id of the sellable related to the received item
    @cvar invoice_number: the invoice number of the receiving order
    @cvar receival_date: the date when the item was received
    @cvar quantity: the received quantity
    @cvar cost: the product cost
    @cvar unit_description: the product unit description
    @cvar supplier_name: the product supplier name
    """
    columns = dict(
        id=ReceivingOrderItem.q.id,
        order_id=ReceivingOrder.q.id,
        purchase_id=ReceivingOrder.q.purchaseID,
        purchase_item_id=ReceivingOrderItem.q.purchase_itemID,
        sellable_id=ReceivingOrderItem.q.sellableID,
        invoice_number=ReceivingOrder.q.invoice_number,
        receival_date=ReceivingOrder.q.receival_date,
        quantity=ReceivingOrderItem.q.quantity,
        cost=ReceivingOrderItem.q.cost,
        unit_description=SellableUnit.q.description,
        supplier_name=Person.q.name,
    )

    joins = [
        LEFTJOINOn(None, ReceivingOrder,
                   ReceivingOrderItem.q.receiving_orderID == ReceivingOrder.q.id),
        LEFTJOINOn(None, Sellable,
                   ReceivingOrderItem.q.sellableID == Sellable.q.id),
        LEFTJOINOn(None, SellableUnit,
                   Sellable.q.unitID == SellableUnit.q.id),
        LEFTJOINOn(None, PersonAdaptToSupplier,
                   ReceivingOrder.q.supplierID == PersonAdaptToSupplier.q.id),
        LEFTJOINOn(None, Person,
                   PersonAdaptToSupplier.q._originalID == Person.q.id),
    ]
