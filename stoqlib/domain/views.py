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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

from stoqlib.database.orm import const, AND, INNERJOINOn, LEFTJOINOn, OR
from stoqlib.database.orm import Viewable, Field, Alias
from stoqlib.domain.account import Account, AccountTransaction
from stoqlib.domain.commission import CommissionSource
from stoqlib.domain.loan import Loan, LoanItem
from stoqlib.domain.person import (Person, PersonAdaptToSupplier,
                                   PersonAdaptToUser, PersonAdaptToBranch,
                                   PersonAdaptToClient, PersonAdaptToEmployee)
from stoqlib.domain.product import (Product,
                                    ProductAdaptToStorable,
                                    ProductStockItem,
                                    ProductHistory,
                                    ProductComponent)
from stoqlib.domain.production import ProductionOrder, ProductionItem
from stoqlib.domain.purchase import (Quotation, QuoteGroup, PurchaseOrder,
                                     PurchaseItem)
from stoqlib.domain.receiving import ReceivingOrderItem, ReceivingOrder
from stoqlib.domain.sale import SaleItem, Sale
from stoqlib.domain.sellable import (Sellable, SellableUnit,
                                     SellableCategory,
                                     SellableTaxConstant)
from stoqlib.domain.stockdecrease import (StockDecrease, StockDecreaseItem)


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
        description=Sellable.q.description,
        product_id=Product.q.id,
        location=Product.q.location,
        tax_description=SellableTaxConstant.q.description,
        category_description=SellableCategory.q.description,
        total_stock_cost=const.SUM(
                ProductStockItem.q.stock_cost * ProductStockItem.q.quantity),
        stock=const.COALESCE(const.SUM(ProductStockItem.q.quantity +
                                       ProductStockItem.q.logic_quantity), 0),
        unit=SellableUnit.q.description,
        )

    joins = [
        # Tax Constant
        LEFTJOINOn(None, SellableTaxConstant,
                   SellableTaxConstant.q.id == Sellable.q.tax_constantID),
        # Category
        LEFTJOINOn(None, SellableCategory,
                   SellableCategory.q.id == Sellable.q.categoryID),
        # SellableUnit
        LEFTJOINOn(None, SellableUnit,
                   Sellable.q.unitID == SellableUnit.q.id),
        # Product
        INNERJOINOn(None, Product,
                    Product.q.sellableID == Sellable.q.id),
        # Product Stock Item
        LEFTJOINOn(None, ProductAdaptToStorable,
                   ProductAdaptToStorable.q.originalID == Product.q.id),
        LEFTJOINOn(None, ProductStockItem,
                   ProductStockItem.q.storableID ==
                   ProductAdaptToStorable.q.id),
        ]

    clause = Sellable.q.status != Sellable.STATUS_CLOSED

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
    def sellable(self):
        return Sellable.get(self.id, connection=self.get_connection())

    @property
    def product(self):
        return Product.get(self.product_id, connection=self.get_connection())

    @property
    def stock_cost(self):
        if self.stock:
            return self.total_stock_cost / self.stock

        return 0

    @property
    def price(self):
        # This property is needed because the price value in the view column
        # might not be the price used (check on_sale_* properties on Sellable).
        # FIXME: This could be done here, without the extra query
        sellable = Sellable.get(self.id, connection=self.get_connection())
        return sellable.price


class ProductFullWithClosedStockView(ProductFullStockView):
    """Stores information about products, showing the closed ones too.
    """

    clause = None


class ProductClosedStockView(ProductFullWithClosedStockView):
    """Stores information about products that were closed.
    """

    clause = Sellable.q.status == Sellable.STATUS_CLOSED


class ProductComponentView(ProductFullStockView):
    columns = ProductFullStockView.columns
    clause = AND(ProductFullStockView.clause,
                 ProductComponent.q.productID == Product.q.id, )

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
        purchase_id=PurchaseOrder.q.id,
        to_receive=const.SUM(PurchaseItem.q.quantity -
                             PurchaseItem.q.quantity_received)
    )

    joins = [
        LEFTJOINOn(None, PurchaseOrder,
                   PurchaseOrder.q.id == PurchaseItem.q.orderID)]

    clause = PurchaseOrder.q.status == PurchaseOrder.ORDER_CONFIRMED


class ProductFullStockItemView(ProductFullStockView):
    # ProductFullStockView already joins with a 1 to Many table (Sellable
    # with ProductStockItem).
    #
    # This is why we must join PurchaseItem (another 1 to many table) in a
    # subquery
    _purchase_total = Alias(_PurchaseItemTotal, '_purchase_total')

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
        description=Sellable.q.description,
        branch=ProductHistory.q.branchID,
        sold_date=ProductHistory.q.sold_date,
        received_date=ProductHistory.q.received_date,
        production_date=ProductHistory.q.production_date,
        decreased_date=ProductHistory.q.decreased_date,
        quantity_sold=const.SUM(ProductHistory.q.quantity_sold),
        quantity_received=const.SUM(ProductHistory.q.quantity_received),
        quantity_transfered=const.SUM(ProductHistory.q.quantity_transfered),
        quantity_produced=const.SUM(ProductHistory.q.quantity_produced),
        quantity_consumed=const.SUM(ProductHistory.q.quantity_consumed),
        quantity_lost=const.SUM(ProductHistory.q.quantity_lost),
        quantity_decreased=const.SUM(ProductHistory.q.quantity_decreased),
        )

    hidden_columns = ['sold_date', 'received_date', 'production_date',
                      'decreased_date']

    joins = [
        INNERJOINOn(None, Sellable,
                    ProductHistory.q.sellableID == Sellable.q.id),
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
        description=Sellable.q.description,
        unit=SellableUnit.q.description,
        product_id=Product.q.id,
        category_description=SellableCategory.q.description,
        base_price=Sellable.q.base_price,
        max_discount=Sellable.q.max_discount,
        stock=const.COALESCE(const.SUM(ProductStockItem.q.quantity +
                                       ProductStockItem.q.logic_quantity), 0),
        )

    joins = [
        # Sellable unit
        LEFTJOINOn(None, SellableUnit,
                   SellableUnit.q.id == Sellable.q.unitID),
        # Category
        LEFTJOINOn(None, SellableCategory,
                   SellableCategory.q.id == Sellable.q.categoryID),
        # Product
        LEFTJOINOn(None, Product,
                   Product.q.sellableID == Sellable.q.id),
        # Product Stock Item
        LEFTJOINOn(None, ProductAdaptToStorable,
                   ProductAdaptToStorable.q.originalID == Product.q.id),
        LEFTJOINOn(None, ProductStockItem,
                   ProductStockItem.q.storableID ==
                   ProductAdaptToStorable.q.id),
        ]

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

    @property
    def sellable(self):
        return Sellable.get(self.id, connection=self.get_connection())

    @property
    def price(self):
        # This property is needed because the price value in the view column
        # might not be the price used (check on_sale_* properties on Sellable).
        # FIXME: This could be done here, without the extra query
        sellable = Sellable.get(self.id, connection=self.get_connection())
        return sellable.price


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
                   PersonAdaptToSupplier.q.originalID),
    ]

    clause = QuoteGroup.q.id == Quotation.q.groupID

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


class SoldItemView(Viewable):
    """Stores information about all sale items, including the average cost
    of the sold items.
    """
    columns = dict(
        id=Sellable.q.id,
        code=Sellable.q.code,
        description=Sellable.q.description,
        category=SellableCategory.q.description,
        quantity=const.SUM(SaleItem.q.quantity),
        total_cost=const.SUM(SaleItem.q.quantity * SaleItem.q.average_cost),
    )

    joins = [
        LEFTJOINOn(None, SaleItem,
                   Sellable.q.id == SaleItem.q.sellableID),
        LEFTJOINOn(None, Sale,
                   SaleItem.q.saleID == Sale.q.id),
        LEFTJOINOn(None, SellableCategory,
                   Sellable.q.categoryID == SellableCategory.q.id),
    ]

    clause = OR(Sale.q.status == Sale.STATUS_CONFIRMED,
                Sale.q.status == Sale.STATUS_PAID,
                Sale.q.status == Sale.STATUS_ORDERED, )

    @classmethod
    def select_by_branch_date(cls, query, branch, date,
                              having=None, connection=None):
        if branch:
            branch_query = Sale.q.branchID == branch.id
            if query:
                query = AND(query, branch_query)
            else:
                query = branch_query

        if date:
            if isinstance(date, tuple):
                date_query = AND(const.DATE(Sale.q.confirm_date) >= date[0],
                                 const.DATE(Sale.q.confirm_date) <= date[1])
            else:
                date_query = const.DATE(Sale.q.confirm_date) == date

            if query:
                query = AND(query, date_query)
            else:
                query = date_query

        return cls.select(query, having=having, connection=connection)

    @property
    def average_cost(self):
        if self.quantity:
            return self.total_cost / self.quantity
        return 0


class StockDecreaseItemsView(Viewable):
    """Stores information about all stock decrease items
    """
    columns = dict(
        id=StockDecreaseItem.q.id,
        date=StockDecrease.q.confirm_date,
        removed_by_name=Person.q.name,
        quantity=StockDecreaseItem.q.quantity,
        sellable=StockDecreaseItem.q.sellableID,
        unit_description=SellableUnit.q.description,
    )

    joins = [
        INNERJOINOn(None, StockDecrease,
                    StockDecreaseItem.q.stock_decreaseID == StockDecrease.q.id),
        LEFTJOINOn(None, Sellable,
                   StockDecreaseItem.q.sellableID == Sellable.q.id),
        LEFTJOINOn(None, SellableUnit,
                   Sellable.q.unitID == SellableUnit.q.id),
        INNERJOINOn(None, PersonAdaptToEmployee,
                   StockDecrease.q.removed_byID == PersonAdaptToEmployee.q.id),
        INNERJOINOn(None, Person,
                   PersonAdaptToEmployee.q.originalID == Person.q.id),
    ]


class SoldItemsByBranchView(SoldItemView):
    """Store information about the all sold items by branch.
    """
    columns = SoldItemView.columns.copy()
    columns.update(dict(
        branch_name=Person.q.name,
        total=const.SUM(SaleItem.q.quantity * SaleItem.q.price),
    ))

    joins = SoldItemView.joins[:]
    joins.append(LEFTJOINOn(None, PersonAdaptToBranch,
                   PersonAdaptToBranch.q.id == Sale.q.branchID))
    joins.append(LEFTJOINOn(None, Person,
                   PersonAdaptToBranch.q.originalID == Person.q.id))

    clause = OR(SoldItemView.clause,
                Sale.q.status == Sale.STATUS_RENEGOTIATED)


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
        description=Sellable.q.description,
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
        LEFTJOINOn(None, Product,
                   Product.q.sellableID == PurchaseItem.q.sellableID),
        LEFTJOINOn(None, ProductAdaptToStorable,
                   ProductAdaptToStorable.q.originalID == Product.q.id),
        LEFTJOINOn(None, ProductStockItem,
                   ProductStockItem.q.storableID == ProductAdaptToStorable.q.id),
    ]

    clause = AND(PurchaseOrder.q.status == PurchaseOrder.ORDER_CONFIRMED,
                 PurchaseOrder.q.branchID == ProductStockItem.q.branchID,
                 PurchaseItem.q.quantity > PurchaseItem.q.quantity_received, )

    @property
    def purchase_item(self):
        return PurchaseItem.get(self.id, connection=self.get_connection())


class ConsignedItemAndStockView(PurchasedItemAndStockView):
    columns = PurchasedItemAndStockView.columns.copy()
    columns.update(dict(
        sold=PurchaseItem.q.quantity_sold,
        returned=PurchaseItem.q.quantity_returned,
    ))
    joins = PurchasedItemAndStockView.joins[:]
    clause = AND(PurchaseOrder.q.consigned == True,
                 PurchaseOrder.q.branchID == ProductStockItem.q.branchID)


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
                   _PurchaseUser.q.originalID == _PurchaseResponsible.q.id),
        LEFTJOINOn(None, PersonAdaptToSupplier,
                   ReceivingOrder.q.supplierID == PersonAdaptToSupplier.q.id),
        LEFTJOINOn(None, _Supplier,
                   PersonAdaptToSupplier.q.originalID == _Supplier.q.id),
        LEFTJOINOn(None, PersonAdaptToUser,
                   ReceivingOrder.q.responsibleID == PersonAdaptToUser.q.id),
        LEFTJOINOn(None, _Responsible,
                   PersonAdaptToUser.q.originalID == _Responsible.q.id),
    ]


class SaleItemsView(Viewable):
    """Show information about sold items and about the corresponding sale.
    This is slightlig difrent than SoldItemView that groups sold items from
    diferent sales.
    """

    columns = dict(
        id=SaleItem.q.id,
        sellable_id=Sellable.q.id,
        code=Sellable.q.code,
        description=Sellable.q.description,
        sale_id=SaleItem.q.saleID,
        sale_date=Sale.q.open_date,
        client_name=Person.q.name,
        quantity=SaleItem.q.quantity,
        unit_description=SellableUnit.q.description,
    )

    joins = [
        LEFTJOINOn(None, Sellable,
                    Sellable.q.id == SaleItem.q.sellableID),
        LEFTJOINOn(None, Sale,
                   SaleItem.q.saleID == Sale.q.id),
        LEFTJOINOn(None, SellableUnit,
                   Sellable.q.unitID == SellableUnit.q.id),
        LEFTJOINOn(None, PersonAdaptToClient,
                   Sale.q.clientID == PersonAdaptToClient.q.id),
        LEFTJOINOn(None, Person,
                   PersonAdaptToClient.q.originalID == Person.q.id),
    ]

    clause = OR(Sale.q.status == Sale.STATUS_CONFIRMED,
                Sale.q.status == Sale.STATUS_PAID,
                Sale.q.status == Sale.STATUS_RENEGOTIATED,
                Sale.q.status == Sale.STATUS_ORDERED)


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
                   PersonAdaptToSupplier.q.originalID == Person.q.id),
    ]


class ProductionItemView(Viewable):
    columns = dict(id=ProductionItem.q.id,
                   order_id=ProductionOrder.q.id,
                   order_status=ProductionOrder.q.status,
                   quantity=ProductionItem.q.quantity,
                   produced=ProductionItem.q.produced,
                   lost=ProductionItem.q.lost,
                   category_description=SellableCategory.q.description,
                   unit_description=SellableUnit.q.description,
                   description=Sellable.q.description, )

    joins = [
        LEFTJOINOn(None, ProductionOrder,
                   ProductionItem.q.orderID == ProductionOrder.q.id),
        LEFTJOINOn(None, Product,
                   ProductionItem.q.productID == Product.q.id),
        LEFTJOINOn(None, Sellable,
                    Sellable.q.id == Product.q.sellableID),
        LEFTJOINOn(None, SellableCategory,
                   SellableCategory.q.id == Sellable.q.categoryID),
        LEFTJOINOn(None, SellableUnit,
                   Sellable.q.unitID == SellableUnit.q.id),
    ]

    @property
    def production_item(self):
        return ProductionItem.get(self.id, connection=self.get_connection())


class LoanView(Viewable):
    PersonBranch = Alias(Person, 'person_branch')
    PersonResponsible = Alias(Person, 'person_responsible')
    PersonClient = Alias(Person, 'person_client')

    columns = dict(id=Loan.q.id,
                    status=Loan.q.status,
                    open_date=Loan.q.open_date,
                    close_date=Loan.q.close_date,
                    expire_date=Loan.q.expire_date,

                    removed_by=Loan.q.removed_by,
                    branch_name=PersonBranch.q.name,
                    responsible_name=PersonResponsible.q.name,
                    client_name=PersonClient.q.name,
                    loaned=const.SUM(LoanItem.q.quantity),
                    total=const.SUM(LoanItem.q.quantity * LoanItem.q.price), )
    joins = [
        INNERJOINOn(None, LoanItem, Loan.q.id == LoanItem.q.loanID),
        LEFTJOINOn(None, PersonAdaptToBranch,
                   Loan.q.branchID == PersonAdaptToBranch.q.id),
        LEFTJOINOn(None, PersonAdaptToUser,
                   Loan.q.responsibleID == PersonAdaptToUser.q.id),
        LEFTJOINOn(None, PersonAdaptToClient,
                   Loan.q.clientID == PersonAdaptToClient.q.id),

        LEFTJOINOn(None, PersonBranch,
                   PersonAdaptToBranch.q.originalID == PersonBranch.q.id),
        LEFTJOINOn(None, PersonResponsible,
                   PersonAdaptToUser.q.originalID == PersonResponsible.q.id),
        LEFTJOINOn(None, PersonClient,
                   PersonAdaptToClient.q.originalID == PersonClient.q.id),
    ]


class LoanItemView(Viewable):
    columns = dict(id=LoanItem.q.id,
                   loan_id=Loan.q.id,
                   loan_status=Loan.q.status,
                   opened=Loan.q.open_date,
                   closed=Loan.q.close_date,
                   quantity=LoanItem.q.quantity,
                   sale_quantity=LoanItem.q.sale_quantity,
                   return_quantity=LoanItem.q.return_quantity,
                   price=LoanItem.q.price,
                   total=LoanItem.q.quantity * LoanItem.q.price,
                   sellable_id=Sellable.q.id,
                   code=Sellable.q.code,
                   category_description=SellableCategory.q.description,
                   unit_description=SellableUnit.q.description,
                   description=Sellable.q.description, )

    joins = [
        LEFTJOINOn(None, Loan, LoanItem.q.loanID == Loan.q.id),
        LEFTJOINOn(None, Sellable,
                   LoanItem.q.sellableID == Sellable.q.id),
        LEFTJOINOn(None, SellableUnit,
                   Sellable.q.unitID == SellableUnit.q.id),
        LEFTJOINOn(None, SellableCategory,
                   SellableCategory.q.id == Sellable.q.categoryID),
    ]


class AccountView(Viewable):

    class _SourceSum(Viewable):
        columns = dict(
             id=AccountTransaction.q.source_accountID,
             value=const.SUM(AccountTransaction.q.value),
             )

        joins = []

    class _DestSum(Viewable):
        columns = dict(
             id=AccountTransaction.q.accountID,
             value=const.SUM(AccountTransaction.q.value),
              )

        joins = []

    columns = dict(
        id=Account.q.id,
        parentID=Account.q.parentID,
        account_type=Account.q.account_type,
        dest_accountID=Account.q.parentID,
        description=Account.q.description,
        code=Account.q.code,
        source_value=Field('source_sum', 'value'),
        dest_value=Field('dest_sum', 'value')
        )

    joins = [
        LEFTJOINOn(None, Alias(_SourceSum, 'source_sum'),
                   Field('source_sum', 'id') == Account.q.id),
        LEFTJOINOn(None, Alias(_DestSum, 'dest_sum'),
                   Field('dest_sum', 'id') == Account.q.id),
        ]

    @property
    def account(self):
        """Get the account for this view"""
        return Account.get(self.id, connection=self.get_connection())

    @property
    def parent_account(self):
        """Get the parent account for this view"""
        return Account.get(self.parentID, connection=self.get_connection())

    def matches(self, account_id):
        """Returns true if the account_id matches this account or its parent"""
        if self.id == account_id:
            return True
        if self.parentID and self.parentID == account_id:
            return True
        return False

    def get_combined_value(self):
        """Returns the combined value of incoming and outgoing
        transactions"""
        if self.dest_value is None and self.source_value is None:
            return 0
        elif self.dest_value is None:
            return -self.source_value
        elif self.source_value is None:
            return self.dest_value
        else:
            return self.dest_value - self.source_value

    def __repr__(self):
        return '<AccountView %s>' % (self.description, )
