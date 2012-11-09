# -*- Mode: Python; coding: utf-8 -*-
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

import datetime

from stoqlib.database.orm import const, AND, Join, LeftJoin, OR
from stoqlib.database.orm import Viewable, Field, Alias
from stoqlib.domain.account import Account, AccountTransaction
from stoqlib.domain.address import Address
from stoqlib.domain.commission import CommissionSource
from stoqlib.domain.loan import Loan, LoanItem
from stoqlib.domain.person import (Person, Supplier,
                                   LoginUser, Branch,
                                   Client, Employee,
                                   Transporter)
from stoqlib.domain.product import (Product,
                                    ProductStockItem,
                                    ProductHistory,
                                    ProductComponent,
                                    ProductManufacturer,
                                    Storable)
from stoqlib.domain.production import ProductionOrder, ProductionItem
from stoqlib.domain.purchase import (Quotation, QuoteGroup, PurchaseOrder,
                                     PurchaseItem)
from stoqlib.domain.receiving import ReceivingOrderItem, ReceivingOrder
from stoqlib.domain.sale import SaleItem, Sale, Delivery
from stoqlib.domain.sellable import (Sellable, SellableUnit,
                                     SellableCategory,
                                     SellableTaxConstant)
from stoqlib.domain.stockdecrease import (StockDecrease, StockDecreaseItem)
from stoqlib.lib.decorators import cached_property
from stoqlib.lib.validators import is_date_in_interval


class ProductFullStockView(Viewable):
    """Stores information about products.
    This view is used to query stock information on a certain branch.

    :cvar id: the id of the asellable table
    :cvar barcode: the sellable barcode
    :cvar status: the sellable status
    :cvar cost: the sellable cost
    :cvar price: the sellable price
    :cvar description: the sellable description
    :cvar unit: the unit of the product
    :cvar product_id: the id of the product table
    :cvar location: the location of the product
    :cvar branch_id: the id of branch table
    :cvar stock: the stock of the product
     """

    columns = dict(
        id=Sellable.q.id,
        code=Sellable.q.code,
        barcode=Sellable.q.barcode,
        status=Sellable.q.status,
        cost=Sellable.q.cost,
        description=Sellable.q.description,
        image_id=Sellable.q.image_id,
        base_price=Sellable.q.base_price,
        on_sale_price=Sellable.q.on_sale_price,
        on_sale_start_date=Sellable.q.on_sale_start_date,
        on_sale_end_date=Sellable.q.on_sale_end_date,
        product_id=Product.q.id,
        location=Product.q.location,
        manufacturer=ProductManufacturer.q.name,
        model=Product.q.model,
        tax_description=SellableTaxConstant.q.description,
        category_description=SellableCategory.q.description,
        total_stock_cost=const.SUM(
                ProductStockItem.q.stock_cost * ProductStockItem.q.quantity),
        stock=const.COALESCE(const.SUM(ProductStockItem.q.quantity), 0),
        unit=SellableUnit.q.description,
        )

    joins = [
        # Tax Constant
        LeftJoin(SellableTaxConstant,
                   SellableTaxConstant.q.id == Sellable.q.tax_constant_id),
        # Category
        LeftJoin(SellableCategory,
                   SellableCategory.q.id == Sellable.q.category_id),
        # SellableUnit
        LeftJoin(SellableUnit,
                   Sellable.q.unit_id == SellableUnit.q.id),
        # Product
        Join(Product,
                    Product.q.sellable_id == Sellable.q.id),
        # Product Stock Item
        LeftJoin(Storable,
                   Storable.q.product_id == Product.q.id),
        LeftJoin(ProductStockItem,
                   ProductStockItem.q.storable_id == Storable.q.id),
        # Manufacturer
        LeftJoin(ProductManufacturer,
                   Product.q.manufacturer_id == ProductManufacturer.q.id),
        ]

    clause = Sellable.q.status != Sellable.STATUS_CLOSED

    @classmethod
    def post_search_callback(cls, sresults):
        select = sresults.get_select_expr(const.COUNT(const.DISTINCT(Sellable.q.id)),
                                  const.COALESCE(const.SUM(ProductStockItem.q.quantity), 0))
        return ('count', 'sum'), select

    @classmethod
    def select_by_branch(cls, query, branch, having=None, connection=None):
        if branch:
            # Also show products that were never purchased.
            branch_query = OR(ProductStockItem.q.branch_id == branch.id,
                              ProductStockItem.q.branch_id == None)
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
        # See Sellable.price property
        if self.on_sale_price:
            today = datetime.datetime.today()
            start_date = self.on_sale_start_date
            end_date = self.on_sale_end_date
            if is_date_in_interval(today, start_date, end_date):
                return self.on_sale_price
        return self.base_price

    @property
    def has_image(self):
        return self.image_id is not None


class ProductFullWithClosedStockView(ProductFullStockView):
    """Stores information about products, showing the closed ones too.
    """

    clause = None


class ProductClosedStockView(ProductFullWithClosedStockView):
    """Stores information about products that were closed.
    """

    clause = Sellable.q.status == Sellable.STATUS_CLOSED


class ProductComponentView(ProductFullStockView):
    """Stores information about production products"""

    joins = ProductFullStockView.joins[:]
    joins.extend([
        Join(ProductComponent,
                    ProductComponent.q.product_id == Product.q.id),
        ])


class ProductComponentWithClosedView(ProductComponentView):
    """Stores information about production products, including closed ones"""

    clause = None


class ProductWithStockView(ProductFullStockView):
    """Stores information about products, since product has a purchase or sale.
    This view is used to query stock information on a certain branch.

    :cvar id: the id of the asellable table
    :cvar barcode: the sellable barcode
    :cvar status: the sellable status
    :cvar cost: the sellable cost
    :cvar price: the sellable price
    :cvar description: the sellable description
    :cvar unit: the unit of the product
    :cvar product_id: the id of the product table
    :cvar branch_id: the id of branch table
    :cvar stock: the stock of the product
     """

    clause = AND(
        ProductFullStockView.clause,
        ProductStockItem.q.quantity >= 0,
        )


class _PurchaseItemTotal(Viewable):
    # This subselect should query only from PurchaseItem, otherwise, more one
    # product may appear more than once in the results (if there are purchase
    # orders for it)
    columns = dict(
        id=PurchaseItem.q.sellable_id,
        to_receive=const.SUM(PurchaseItem.q.quantity -
                             PurchaseItem.q.quantity_received)
    )

    joins = [
        LeftJoin(PurchaseOrder,
                 PurchaseOrder.q.id == PurchaseItem.q.order_id)]

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
        minimum_quantity=Storable.q.minimum_quantity,
        maximum_quantity=Storable.q.maximum_quantity,
        to_receive_quantity=Field('_purchase_total', 'to_receive'),
        difference=(const.SUM(ProductStockItem.q.quantity) -
                    Storable.q.minimum_quantity)))

    joins = ProductFullStockView.joins[:]
    joins.append(LeftJoin(_purchase_total,
                            Field('_purchase_total', 'id') == Sellable.q.id))


class ProductQuantityView(Viewable):
    """Stores information about products solded and received.

    :cvar id: the id of the sellable_id of products_quantity table
    :cvar description: the product description
    :cvar branch_id: the id of branch table
    :cvar quantity_sold: the quantity solded of product
    :cvar quantity_transfered: the quantity transfered of product
    :cvar quantity_received: the quantity received of product
    :cvar branch: the id of the branch_id of producst_quantity table
    :cvar date_sale: the date of product's sale
    :cvar date_received: the date of product's received
     """

    columns = dict(
        id=ProductHistory.q.sellable_id,
        code=Sellable.q.code,
        description=Sellable.q.description,
        branch=ProductHistory.q.branch_id,
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
        Join(Sellable,
                    ProductHistory.q.sellable_id == Sellable.q.id),
    ]


class SellableFullStockView(Viewable):
    """Stores information about products.
    This view is used to query stock information on a certain branch.

    :cvar id: the id of the asellable table
    :cvar barcode: the sellable barcode
    :cvar status: the sellable status
    :cvar cost: the sellable cost
    :cvar price: the sellable price
    :cvar description: the sellable description
    :cvar unit: the unit of the product or None
    :cvar product_id: the id of the product table or None
    :cvar branch_id: the id of branch table or None
    :cvar stock: the stock of the product or None
     """

    columns = dict(
        id=Sellable.q.id,
        code=Sellable.q.code,
        barcode=Sellable.q.barcode,
        status=Sellable.q.status,
        cost=Sellable.q.cost,
        description=Sellable.q.description,
        on_sale_price=Sellable.q.on_sale_price,
        on_sale_start_date=Sellable.q.on_sale_start_date,
        on_sale_end_date=Sellable.q.on_sale_end_date,
        unit=SellableUnit.q.description,
        product_id=Product.q.id,
        manufacturer=ProductManufacturer.q.name,
        model=Product.q.model,
        category_description=SellableCategory.q.description,
        base_price=Sellable.q.base_price,
        max_discount=Sellable.q.max_discount,
        stock=const.COALESCE(const.SUM(ProductStockItem.q.quantity), 0),
        )

    joins = [
        # Sellable unit
        LeftJoin(SellableUnit,
                   SellableUnit.q.id == Sellable.q.unit_id),
        # Category
        LeftJoin(SellableCategory,
                   SellableCategory.q.id == Sellable.q.category_id),
        # Product
        LeftJoin(Product,
                   Product.q.sellable_id == Sellable.q.id),
        # Product Stock Item
        LeftJoin(Storable,
                   Storable.q.product_id == Product.q.id),
        LeftJoin(ProductStockItem,
                   ProductStockItem.q.storable_id == Storable.q.id),
        # Manufacturer
        LeftJoin(ProductManufacturer,
                   Product.q.manufacturer_id == ProductManufacturer.q.id),
        ]

    @classmethod
    def select_by_branch(cls, query, branch, having=None, connection=None):
        if branch:
            # We need the OR part to be able to list services
            branch_query = OR(ProductStockItem.q.branch_id == branch.id,
                              ProductStockItem.q.branch_id == None)
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
        # See Sellable.price property
        if self.on_sale_price:
            today = datetime.datetime.today()
            start_date = self.on_sale_start_date
            end_date = self.on_sale_end_date
            if is_date_in_interval(today, start_date, end_date):
                return self.on_sale_price
        return self.base_price


class SellableCategoryView(Viewable):
    """Stores information about categories.
       This view is used to query the category with the related
       commission source.
    """

    columns = dict(
        id=SellableCategory.q.id,
        commission=CommissionSource.q.direct_value,
        installments_commission=CommissionSource.q.installments_value,
        parent_id=SellableCategory.q.category_id,
        description=SellableCategory.q.description,
        suggested_markup=SellableCategory.q.suggested_markup,
    )

    joins = [
        # commission source
        LeftJoin(CommissionSource,
                   CommissionSource.q.category_id ==
                   SellableCategory.q.id),
       ]

    @property
    def category(self):
        return SellableCategory.get(self.id,
                                    connection=self.get_connection())

    def get_parent(self):
        if not self.parent_id:
            return None

        category_views = SellableCategoryView.select(
            connection=self.get_connection(),
            clause=SellableCategoryView.q.id == self.parent_id)
        return category_views[0]

    def get_suggested_markup(self):
        return self._suggested_markup

    @cached_property(ttl=0)
    def _suggested_markup(self):
        category = self
        while category:
            # Compare to None as suggested_markup can be 0
            if category.suggested_markup is not None:
                return category.suggested_markup

            category = category.get_parent()

    def get_commission(self):
        # Compare to None as commission can be 0
        if self.commission is not None:
            return self.commission

        source = self._parent_source_commission
        if source:
            return source.direct_value

    def get_installments_commission(self):
        # Compare to None as commission can be 0
        if self.commission is not None:
            return self.installments_commission

        source = self._parent_source_commission
        if source:
            return source.installments_value

    @cached_property(ttl=0)
    def _parent_source_commission(self):
        parent = self.get_parent()
        while parent:
            source = CommissionSource.selectOneBy(
                category=parent.category, connection=self.get_connection())
            if source:
                return source

            parent = parent.get_parent()


class QuotationView(Viewable):
    """Stores information about the quote group and its quotes.
    """
    columns = dict(
        id=Quotation.q.id,
        purchase_id=Quotation.q.purchase_id,
        group_id=Quotation.q.group_id,
        identifier=Quotation.q.identifier,
        group_identifier=QuoteGroup.q.identifier,
        open_date=PurchaseOrder.q.open_date,
        deadline=PurchaseOrder.q.quote_deadline,
        supplier_name=Person.q.name,
    )

    joins = [
        Join(QuoteGroup,
                    QuoteGroup.q.id == Quotation.q.group_id),
        LeftJoin(PurchaseOrder,
                   PurchaseOrder.q.id == Quotation.q.purchase_id),
        LeftJoin(Supplier,
                   Supplier.q.id == PurchaseOrder.q.supplier_id),
        LeftJoin(Person, Person.q.id ==
                   Supplier.q.person_id),
    ]

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
        LeftJoin(SaleItem,
                   Sellable.q.id == SaleItem.q.sellable_id),
        LeftJoin(Sale,
                   SaleItem.q.sale_id == Sale.q.id),
        LeftJoin(SellableCategory,
                   Sellable.q.category_id == SellableCategory.q.id),
    ]

    clause = OR(Sale.q.status == Sale.STATUS_CONFIRMED,
                Sale.q.status == Sale.STATUS_PAID,
                Sale.q.status == Sale.STATUS_ORDERED, )

    @classmethod
    def select_by_branch_date(cls, query, branch, date,
                              having=None, connection=None):
        if branch:
            branch_query = Sale.q.branch_id == branch.id
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
        quantity=StockDecreaseItem.q.quantity,
        sellable=StockDecreaseItem.q.sellable_id,
        decrease_id=StockDecrease.q.id,
        decrease_identifier=StockDecrease.q.identifier,
        date=StockDecrease.q.confirm_date,
        removed_by_name=Person.q.name,
        unit_description=SellableUnit.q.description,
    )

    joins = [
        Join(StockDecrease,
                    StockDecreaseItem.q.stock_decrease_id == StockDecrease.q.id),
        LeftJoin(Sellable,
                   StockDecreaseItem.q.sellable_id == Sellable.q.id),
        LeftJoin(SellableUnit,
                   Sellable.q.unit_id == SellableUnit.q.id),
        Join(Employee,
                   StockDecrease.q.removed_by_id == Employee.q.id),
        Join(Person,
                   Employee.q.person_id == Person.q.id),
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
    joins.append(LeftJoin(Branch,
                            Branch.q.id == Sale.q.branch_id))
    joins.append(LeftJoin(Person,
                            Branch.q.person_id == Person.q.id))

    clause = OR(SoldItemView.clause,
                Sale.q.status == Sale.STATUS_RENEGOTIATED)


class PurchasedItemAndStockView(Viewable):
    """Stores information about the purchase items that will be delivered and
    also the quantity that is already in stock.
    This view is used to query which products are going to be delivered and if
    they are on time or not.

    :cvar id: the id of the purchased item
    :cvar product_id: the id of the product
    :cvar purchased: the quantity purchased
    :cvar received: the quantity already received
    :cvar stocked: the quantity in stock
    :cvar expected_receival_date: the date that the item might be deliverd
    :cvar purchase_date: the date when the item was purchased
    :cvar branch: the branch where the purchase was done
    """

    columns = dict(
        id=PurchaseItem.q.id,
        product_id=Product.q.id,
        code=Sellable.q.code,
        description=Sellable.q.description,
        purchased=PurchaseItem.q.quantity,
        received=PurchaseItem.q.quantity_received,
        stocked=const.SUM(ProductStockItem.q.quantity),
        expected_receival_date=PurchaseItem.q.expected_receival_date,
        order_identifier=PurchaseOrder.q.identifier,
        purchased_date=PurchaseOrder.q.open_date,
        branch=PurchaseOrder.q.branch_id,
    )

    joins = [
        LeftJoin(PurchaseOrder,
                   PurchaseItem.q.order_id == PurchaseOrder.q.id),
        LeftJoin(Sellable,
                    Sellable.q.id == PurchaseItem.q.sellable_id),
        LeftJoin(Product,
                   Product.q.sellable_id == PurchaseItem.q.sellable_id),
        LeftJoin(Storable,
                   Storable.q.product_id == Product.q.id),
        LeftJoin(ProductStockItem,
                   ProductStockItem.q.storable_id == Storable.q.id),
    ]

    clause = AND(PurchaseOrder.q.status == PurchaseOrder.ORDER_CONFIRMED,
                 PurchaseOrder.q.branch_id == ProductStockItem.q.branch_id,
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
    clause = AND(PurchaseOrder.q.consigned == True,
                 PurchaseOrder.q.branch_id == ProductStockItem.q.branch_id)


class PurchaseReceivingView(Viewable):
    """Stores information about received orders.

    :cvar id: the id of the receiving order
    :cvar receival_date: the date when the receiving order was closed
    :cvar invoice_number: the number of the order that was received
    :cvar invoice_total: the total value of the received order
    :cvar purchase_identifier: the identifier of the received order
    :cvar branch_id: the id branch where the order was received
    :cvar purchase_responsible_name: the one who have confirmed the purchase
    :cvar responsible_name: the one who has received the order
    :cvar supplier_name: the supplier name
    """
    _Responsible = Alias(Person, "responsible")
    _Supplier = Alias(Person, "supplier_person")
    _PurchaseUser = Alias(LoginUser, "purchase_user")
    _PurchaseResponsible = Alias(Person, "purchase_responsible")

    columns = dict(
        id=ReceivingOrder.q.id,
        receival_date=ReceivingOrder.q.receival_date,
        invoice_number=ReceivingOrder.q.invoice_number,
        invoice_total=ReceivingOrder.q.invoice_total,
        purchase_identifier=PurchaseOrder.q.identifier,
        branch_id=ReceivingOrder.q.branch_id,
        purchase_responsible_name=_PurchaseResponsible.q.name,
        responsible_name=_Responsible.q.name,
        supplier_name=_Supplier.q.name,
        )

    joins = [
        LeftJoin(PurchaseOrder,
                   ReceivingOrder.q.purchase_id == PurchaseOrder.q.id),
        LeftJoin(_PurchaseUser,
                   PurchaseOrder.q.responsible_id == _PurchaseUser.q.id),
        LeftJoin(_PurchaseResponsible,
                   _PurchaseUser.q.person_id == _PurchaseResponsible.q.id),
        LeftJoin(Supplier,
                   ReceivingOrder.q.supplier_id == Supplier.q.id),
        LeftJoin(_Supplier,
                   Supplier.q.person_id == _Supplier.q.id),
        LeftJoin(LoginUser,
                   ReceivingOrder.q.responsible_id == LoginUser.q.id),
        LeftJoin(_Responsible,
                   LoginUser.q.person_id == _Responsible.q.id),
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
        sale_id=SaleItem.q.sale_id,
        sale_identifier=Sale.q.identifier,
        sale_date=Sale.q.open_date,
        client_name=Person.q.name,
        quantity=SaleItem.q.quantity,
        unit_description=SellableUnit.q.description,
    )

    joins = [
        LeftJoin(Sellable,
                    Sellable.q.id == SaleItem.q.sellable_id),
        LeftJoin(Sale,
                   SaleItem.q.sale_id == Sale.q.id),
        LeftJoin(SellableUnit,
                   Sellable.q.unit_id == SellableUnit.q.id),
        LeftJoin(Client,
                   Sale.q.client_id == Client.q.id),
        LeftJoin(Person,
                   Client.q.person_id == Person.q.id),
    ]

    clause = OR(Sale.q.status == Sale.STATUS_CONFIRMED,
                Sale.q.status == Sale.STATUS_PAID,
                Sale.q.status == Sale.STATUS_RENEGOTIATED,
                Sale.q.status == Sale.STATUS_ORDERED)


class ReceivingItemView(Viewable):
    """Stores information about receiving items.
    This view is used to query products that are going to be received or was
    already received and the information related to that process.

    :cvar id: the id of the receiving item
    :cvar order_identifier: the identifier of the receiving order
    :cvar purchase_identifier: the identifier of the purchase order
    :cvar purchase_item_id: the id of the purchase item
    :cvar sellable_id: the id of the sellable related to the received item
    :cvar invoice_number: the invoice number of the receiving order
    :cvar receival_date: the date when the item was received
    :cvar quantity: the received quantity
    :cvar cost: the product cost
    :cvar unit_description: the product unit description
    :cvar supplier_name: the product supplier name
    """
    columns = dict(
        id=ReceivingOrderItem.q.id,
        order_identifier=ReceivingOrder.q.identifier,
        purchase_identifier=PurchaseOrder.q.identifier,
        purchase_item_id=ReceivingOrderItem.q.purchase_item_id,
        sellable_id=ReceivingOrderItem.q.sellable_id,
        invoice_number=ReceivingOrder.q.invoice_number,
        receival_date=ReceivingOrder.q.receival_date,
        quantity=ReceivingOrderItem.q.quantity,
        cost=ReceivingOrderItem.q.cost,
        unit_description=SellableUnit.q.description,
        supplier_name=Person.q.name,
    )

    joins = [
        LeftJoin(ReceivingOrder,
                   ReceivingOrderItem.q.receiving_order_id == ReceivingOrder.q.id),
        LeftJoin(PurchaseOrder,
                   ReceivingOrder.q.purchase_id == PurchaseOrder.q.id),
        LeftJoin(Sellable,
                   ReceivingOrderItem.q.sellable_id == Sellable.q.id),
        LeftJoin(SellableUnit,
                   Sellable.q.unit_id == SellableUnit.q.id),
        LeftJoin(Supplier,
                   ReceivingOrder.q.supplier_id == Supplier.q.id),
        LeftJoin(Person,
                   Supplier.q.person_id == Person.q.id),
    ]


class ProductionItemView(Viewable):
    columns = dict(id=ProductionItem.q.id,
                   order_identifier=ProductionOrder.q.identifier,
                   order_status=ProductionOrder.q.status,
                   quantity=ProductionItem.q.quantity,
                   produced=ProductionItem.q.produced,
                   lost=ProductionItem.q.lost,
                   category_description=SellableCategory.q.description,
                   unit_description=SellableUnit.q.description,
                   description=Sellable.q.description, )

    joins = [
        LeftJoin(ProductionOrder,
                   ProductionItem.q.order_id == ProductionOrder.q.id),
        LeftJoin(Product,
                   ProductionItem.q.product_id == Product.q.id),
        LeftJoin(Sellable,
                    Sellable.q.id == Product.q.sellable_id),
        LeftJoin(SellableCategory,
                   SellableCategory.q.id == Sellable.q.category_id),
        LeftJoin(SellableUnit,
                   Sellable.q.unit_id == SellableUnit.q.id),
    ]

    @property
    def production_item(self):
        return ProductionItem.get(self.id, connection=self.get_connection())


class LoanView(Viewable):
    PersonBranch = Alias(Person, 'person_branch')
    PersonResponsible = Alias(Person, 'person_responsible')
    PersonClient = Alias(Person, 'person_client')

    columns = dict(
        id=Loan.q.id,
        identifier=Loan.q.identifier,
        status=Loan.q.status,
        open_date=Loan.q.open_date,
        close_date=Loan.q.close_date,
        expire_date=Loan.q.expire_date,

        removed_by=Loan.q.removed_by,
        branch_name=PersonBranch.q.name,
        responsible_name=PersonResponsible.q.name,
        client_name=PersonClient.q.name,
        loaned=const.SUM(LoanItem.q.quantity),
        total=const.SUM(LoanItem.q.quantity * LoanItem.q.price),
    )
    joins = [
        Join(LoanItem, Loan.q.id == LoanItem.q.loan_id),
        LeftJoin(Branch,
                   Loan.q.branch_id == Branch.q.id),
        LeftJoin(LoginUser,
                   Loan.q.responsible_id == LoginUser.q.id),
        LeftJoin(Client,
                   Loan.q.client_id == Client.q.id),

        LeftJoin(PersonBranch,
                   Branch.q.person_id == PersonBranch.q.id),
        LeftJoin(PersonResponsible,
                   LoginUser.q.person_id == PersonResponsible.q.id),
        LeftJoin(PersonClient,
                   Client.q.person_id == PersonClient.q.id),
    ]

    @property
    def loan(self):
        return Loan.get(self.id, connection=self.get_connection())


class LoanItemView(Viewable):
    columns = dict(
        id=LoanItem.q.id,
        loan_identifier=Loan.q.identifier,
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
        description=Sellable.q.description,
    )

    joins = [
        LeftJoin(Loan, LoanItem.q.loan_id == Loan.q.id),
        LeftJoin(Sellable,
                   LoanItem.q.sellable_id == Sellable.q.id),
        LeftJoin(SellableUnit,
                   Sellable.q.unit_id == SellableUnit.q.id),
        LeftJoin(SellableCategory,
                   SellableCategory.q.id == Sellable.q.category_id),
    ]


class AccountView(Viewable):

    class _SourceSum(Viewable):
        columns = dict(
            id=AccountTransaction.q.source_account_id,
            value=const.SUM(AccountTransaction.q.value),
            )

    class _DestSum(Viewable):
        columns = dict(
            id=AccountTransaction.q.account_id,
            value=const.SUM(AccountTransaction.q.value),
            )

    columns = dict(
        id=Account.q.id,
        parent_id=Account.q.parent_id,
        account_type=Account.q.account_type,
        dest_account_id=Account.q.parent_id,
        description=Account.q.description,
        code=Account.q.code,
        source_value=Field('source_sum', 'value'),
        dest_value=Field('dest_sum', 'value'),
        )

    joins = [
        LeftJoin(Alias(_SourceSum, 'source_sum'),
                   Field('source_sum', 'id') == Account.q.id),
        LeftJoin(Alias(_DestSum, 'dest_sum'),
                   Field('dest_sum', 'id') == Account.q.id),
        ]

    @property
    def account(self):
        """Get the account for this view"""
        return Account.get(self.id, connection=self.get_connection())

    @property
    def parent_account(self):
        """Get the parent account for this view"""
        return Account.get(self.parent_id, connection=self.get_connection())

    def matches(self, account_id):
        """Returns true if the account_id matches this account or its parent"""
        if self.id == account_id:
            return True
        if self.parent_id and self.parent_id == account_id:
            return True
        return False

    def get_combined_value(self):
        """Returns the combined value of incoming and outgoing
        transactions"""
        if not self.dest_value and not self.source_value:
            return 0
        elif not self.dest_value:
            return -self.source_value
        elif not self.source_value:
            return self.dest_value
        else:
            return self.dest_value - self.source_value

    def __repr__(self):
        return '<AccountView %s>' % (self.description, )


class DeliveryView(Viewable):
    PersonTransporter = Alias(Person, 'person_transporter')
    PersonClient = Alias(Person, 'person_client')

    columns = dict(
        # Delivery
        id=Delivery.q.id,
        status=Delivery.q.status,
        tracking_code=Delivery.q.tracking_code,
        open_date=Delivery.q.open_date,
        deliver_date=Delivery.q.deliver_date,
        receive_date=Delivery.q.receive_date,

        # Transporter
        transporter_name=PersonTransporter.q.name,

        # Client
        client_name=PersonClient.q.name,

        # Sale
        sale_identifier=Sale.q.identifier,

        # Address
        address_id=Delivery.q.address_id,
    )

    joins = [
        LeftJoin(Transporter,
                 Transporter.q.id == Delivery.q.transporter_id),
        LeftJoin(PersonTransporter,
                 PersonTransporter.q.id == Transporter.q.person_id),
        LeftJoin(SaleItem,
                 SaleItem.q.id == Delivery.q.service_item_id),
        LeftJoin(Sale,
                 Sale.q.id == SaleItem.q.sale_id),
        LeftJoin(Client,
                 Client.q.id == Sale.q.client_id),
        LeftJoin(PersonClient,
                 PersonClient.q.id == Client.q.person_id),
        #LeftJoin(Address,
        #         Address.q.person_id == Client.q.person_id),
        ]

    @property
    def status_str(self):
        return Delivery.statuses[self.status]

    @property
    def delivery(self):
        return Delivery.get(self.id, connection=self.get_connection())

    @property
    def address_str(self):
        return Address.get(self.address_id,
               connection=self.get_connection()).get_description()
