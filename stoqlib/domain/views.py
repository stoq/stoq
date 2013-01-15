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

from storm.expr import And, Coalesce, Count, Join, LeftJoin, Or, Sum
from storm.info import ClassAlias

from stoqlib.database.expr import Date, Distinct, Field
from stoqlib.database.viewable import Viewable, ViewableAlias
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
        id=Sellable.id,
        code=Sellable.code,
        barcode=Sellable.barcode,
        status=Sellable.status,
        cost=Sellable.cost,
        description=Sellable.description,
        image_id=Sellable.image_id,
        base_price=Sellable.base_price,
        on_sale_price=Sellable.on_sale_price,
        on_sale_start_date=Sellable.on_sale_start_date,
        on_sale_end_date=Sellable.on_sale_end_date,
        product_id=Product.id,
        location=Product.location,
        manufacturer=ProductManufacturer.name,
        model=Product.model,
        tax_description=SellableTaxConstant.description,
        category_description=SellableCategory.description,
        total_stock_cost=Sum(
                ProductStockItem.stock_cost * ProductStockItem.quantity),
        stock=Coalesce(Sum(ProductStockItem.quantity), 0),
        unit=SellableUnit.description,
        )

    joins = [
        # Tax Constant
        LeftJoin(SellableTaxConstant,
                   SellableTaxConstant.id == Sellable.tax_constant_id),
        # Category
        LeftJoin(SellableCategory,
                   SellableCategory.id == Sellable.category_id),
        # SellableUnit
        LeftJoin(SellableUnit,
                   Sellable.unit_id == SellableUnit.id),
        # Product
        Join(Product,
                    Product.sellable_id == Sellable.id),
        # Product Stock Item
        LeftJoin(Storable,
                   Storable.product_id == Product.id),
        LeftJoin(ProductStockItem,
                   ProductStockItem.storable_id == Storable.id),
        # Manufacturer
        LeftJoin(ProductManufacturer,
                   Product.manufacturer_id == ProductManufacturer.id),
        ]

    clause = Sellable.status != Sellable.STATUS_CLOSED

    @classmethod
    def post_search_callback(cls, sresults):
        select = sresults.get_select_expr(Count(Distinct(Sellable.id)),
                                  Coalesce(Sum(ProductStockItem.quantity), 0))
        return ('count', 'sum'), select

    @classmethod
    def select_by_branch(cls, query, branch, having=None, store=None):
        if branch:
            # Also show products that were never purchased.
            branch_query = Or(ProductStockItem.branch_id == branch.id,
                              ProductStockItem.branch_id == None)
            if query:
                query = And(query, branch_query)
            else:
                query = branch_query

        return cls.select(query, having=having, store=store)

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
        return Sellable.get(self.id, store=self.store)

    @property
    def product(self):
        return Product.get(self.product_id, store=self.store)

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

    clause = Sellable.status == Sellable.STATUS_CLOSED


class ProductComponentView(ProductFullStockView):
    """Stores information about production products"""

    joins = ProductFullStockView.joins[:]
    joins.extend([
        Join(ProductComponent,
                    ProductComponent.product_id == Product.id),
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

    clause = And(
        ProductFullStockView.clause,
        ProductStockItem.quantity >= 0,
        )


class _PurchaseItemTotal(Viewable):
    # This subselect should query only from PurchaseItem, otherwise, more one
    # product may appear more than once in the results (if there are purchase
    # orders for it)
    columns = dict(
        id=PurchaseItem.sellable_id,
        to_receive=Sum(PurchaseItem.quantity -
                             PurchaseItem.quantity_received)
    )

    joins = [
        LeftJoin(PurchaseOrder,
                 PurchaseOrder.id == PurchaseItem.order_id)]

    clause = PurchaseOrder.status == PurchaseOrder.ORDER_CONFIRMED


class ProductFullStockItemView(ProductFullStockView):
    # ProductFullStockView already joins with a 1 to Many table (Sellable
    # with ProductStockItem).
    #
    # This is why we must join PurchaseItem (another 1 to many table) in a
    # subquery
    _purchase_total = ViewableAlias(_PurchaseItemTotal, '_purchase_total')

    columns = ProductFullStockView.columns.copy()
    columns.update(dict(
        minimum_quantity=Storable.minimum_quantity,
        maximum_quantity=Storable.maximum_quantity,
        to_receive_quantity=Field('_purchase_total', 'to_receive'),
        difference=(Sum(ProductStockItem.quantity) -
                    Storable.minimum_quantity)))

    joins = ProductFullStockView.joins[:]
    joins.append(LeftJoin(_purchase_total,
                            Field('_purchase_total', 'id') == Sellable.id))


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
        id=ProductHistory.sellable_id,
        code=Sellable.code,
        description=Sellable.description,
        branch=ProductHistory.branch_id,
        sold_date=ProductHistory.sold_date,
        received_date=ProductHistory.received_date,
        production_date=ProductHistory.production_date,
        decreased_date=ProductHistory.decreased_date,
        quantity_sold=Sum(ProductHistory.quantity_sold),
        quantity_received=Sum(ProductHistory.quantity_received),
        quantity_transfered=Sum(ProductHistory.quantity_transfered),
        quantity_produced=Sum(ProductHistory.quantity_produced),
        quantity_consumed=Sum(ProductHistory.quantity_consumed),
        quantity_lost=Sum(ProductHistory.quantity_lost),
        quantity_decreased=Sum(ProductHistory.quantity_decreased),
        )

    hidden_columns = ['sold_date', 'received_date', 'production_date',
                      'decreased_date']

    joins = [
        Join(Sellable,
                    ProductHistory.sellable_id == Sellable.id),
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
        id=Sellable.id,
        code=Sellable.code,
        barcode=Sellable.barcode,
        status=Sellable.status,
        cost=Sellable.cost,
        description=Sellable.description,
        on_sale_price=Sellable.on_sale_price,
        on_sale_start_date=Sellable.on_sale_start_date,
        on_sale_end_date=Sellable.on_sale_end_date,
        unit=SellableUnit.description,
        product_id=Product.id,
        manufacturer=ProductManufacturer.name,
        model=Product.model,
        category_description=SellableCategory.description,
        base_price=Sellable.base_price,
        max_discount=Sellable.max_discount,
        stock=Coalesce(Sum(ProductStockItem.quantity), 0),
        )

    joins = [
        # Sellable unit
        LeftJoin(SellableUnit,
                   SellableUnit.id == Sellable.unit_id),
        # Category
        LeftJoin(SellableCategory,
                   SellableCategory.id == Sellable.category_id),
        # Product
        LeftJoin(Product,
                   Product.sellable_id == Sellable.id),
        # Product Stock Item
        LeftJoin(Storable,
                   Storable.product_id == Product.id),
        LeftJoin(ProductStockItem,
                   ProductStockItem.storable_id == Storable.id),
        # Manufacturer
        LeftJoin(ProductManufacturer,
                   Product.manufacturer_id == ProductManufacturer.id),
        ]

    @classmethod
    def select_by_branch(cls, query, branch, having=None, store=None):
        if branch:
            # We need the OR part to be able to list services
            branch_query = Or(ProductStockItem.branch_id == branch.id,
                              ProductStockItem.branch_id == None)
            if query:
                query = And(query, branch_query)
            else:
                query = branch_query

        return cls.select(query, having=having, store=store)

    @property
    def sellable(self):
        return Sellable.get(self.id, store=self.store)

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
        id=SellableCategory.id,
        commission=CommissionSource.direct_value,
        installments_commission=CommissionSource.installments_value,
        parent_id=SellableCategory.category_id,
        description=SellableCategory.description,
        suggested_markup=SellableCategory.suggested_markup,
    )

    joins = [
        # commission source
        LeftJoin(CommissionSource,
                   CommissionSource.category_id ==
                   SellableCategory.id),
       ]

    @property
    def category(self):
        return SellableCategory.get(self.id,
                                    store=self.store)

    def get_parent(self):
        if not self.parent_id:
            return None

        category_views = SellableCategoryView.select(
            store=self.store,
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
            store = self.store
            source = store.find(CommissionSource,
                                category=parent.category).one()
            if source:
                return source

            parent = parent.get_parent()


class QuotationView(Viewable):
    """Stores information about the quote group and its quotes.
    """
    columns = dict(
        id=Quotation.id,
        purchase_id=Quotation.purchase_id,
        group_id=Quotation.group_id,
        identifier=Quotation.identifier,
        group_identifier=QuoteGroup.identifier,
        open_date=PurchaseOrder.open_date,
        deadline=PurchaseOrder.quote_deadline,
        supplier_name=Person.name,
    )

    joins = [
        Join(QuoteGroup,
                    QuoteGroup.id == Quotation.group_id),
        LeftJoin(PurchaseOrder,
                   PurchaseOrder.id == Quotation.purchase_id),
        LeftJoin(Supplier,
                   Supplier.id == PurchaseOrder.supplier_id),
        LeftJoin(Person, Person.id ==
                   Supplier.person_id),
    ]

    @property
    def group(self):
        return QuoteGroup.get(self.group_id, store=self.store)

    @property
    def quotation(self):
        return Quotation.get(self.id, store=self.store)

    @property
    def purchase(self):
        return PurchaseOrder.get(self.purchase_id,
                                 store=self.store)


class SoldItemView(Viewable):
    """Stores information about all sale items, including the average cost
    of the sold items.
    """
    columns = dict(
        id=Sellable.id,
        code=Sellable.code,
        description=Sellable.description,
        category=SellableCategory.description,
        quantity=Sum(SaleItem.quantity),
        total_cost=Sum(SaleItem.quantity * SaleItem.average_cost),
    )

    joins = [
        LeftJoin(SaleItem,
                   Sellable.id == SaleItem.sellable_id),
        LeftJoin(Sale,
                   SaleItem.sale_id == Sale.id),
        LeftJoin(SellableCategory,
                   Sellable.category_id == SellableCategory.id),
    ]

    clause = Or(Sale.status == Sale.STATUS_CONFIRMED,
                Sale.status == Sale.STATUS_PAID,
                Sale.status == Sale.STATUS_ORDERED, )

    @classmethod
    def select_by_branch_date(cls, query, branch, date,
                              having=None, store=None):
        if branch:
            branch_query = Sale.branch_id == branch.id
            if query:
                query = And(query, branch_query)
            else:
                query = branch_query

        if date:
            if isinstance(date, tuple):
                date_query = And(Date(Sale.confirm_date) >= date[0],
                                 Date(Sale.confirm_date) <= date[1])
            else:
                date_query = Date(Sale.confirm_date) == date

            if query:
                query = And(query, date_query)
            else:
                query = date_query

        return cls.select(query, having=having, store=store)

    @property
    def average_cost(self):
        if self.quantity:
            return self.total_cost / self.quantity
        return 0


class StockDecreaseItemsView(Viewable):
    """Stores information about all stock decrease items
    """
    columns = dict(
        id=StockDecreaseItem.id,
        quantity=StockDecreaseItem.quantity,
        sellable=StockDecreaseItem.sellable_id,
        decrease_id=StockDecrease.id,
        decrease_identifier=StockDecrease.identifier,
        date=StockDecrease.confirm_date,
        removed_by_name=Person.name,
        unit_description=SellableUnit.description,
    )

    joins = [
        Join(StockDecrease,
                    StockDecreaseItem.stock_decrease_id == StockDecrease.id),
        LeftJoin(Sellable,
                   StockDecreaseItem.sellable_id == Sellable.id),
        LeftJoin(SellableUnit,
                   Sellable.unit_id == SellableUnit.id),
        Join(Employee,
                   StockDecrease.removed_by_id == Employee.id),
        Join(Person,
                   Employee.person_id == Person.id),
    ]


class SoldItemsByBranchView(SoldItemView):
    """Store information about the all sold items by branch.
    """
    columns = SoldItemView.columns.copy()
    columns.update(dict(
        branch_name=Person.name,
        total=Sum(SaleItem.quantity * SaleItem.price),
    ))

    joins = SoldItemView.joins[:]
    joins.append(LeftJoin(Branch,
                            Branch.id == Sale.branch_id))
    joins.append(LeftJoin(Person,
                            Branch.person_id == Person.id))

    clause = Or(SoldItemView.clause,
                Sale.status == Sale.STATUS_RENEGOTIATED)


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
        id=PurchaseItem.id,
        product_id=Product.id,
        code=Sellable.code,
        description=Sellable.description,
        purchased=PurchaseItem.quantity,
        received=PurchaseItem.quantity_received,
        stocked=Sum(ProductStockItem.quantity),
        expected_receival_date=PurchaseItem.expected_receival_date,
        order_identifier=PurchaseOrder.identifier,
        purchased_date=PurchaseOrder.open_date,
        branch=PurchaseOrder.branch_id,
    )

    joins = [
        LeftJoin(PurchaseOrder,
                   PurchaseItem.order_id == PurchaseOrder.id),
        LeftJoin(Sellable,
                    Sellable.id == PurchaseItem.sellable_id),
        LeftJoin(Product,
                   Product.sellable_id == PurchaseItem.sellable_id),
        LeftJoin(Storable,
                   Storable.product_id == Product.id),
        LeftJoin(ProductStockItem,
                   ProductStockItem.storable_id == Storable.id),
    ]

    clause = And(PurchaseOrder.status == PurchaseOrder.ORDER_CONFIRMED,
                 PurchaseOrder.branch_id == ProductStockItem.branch_id,
                 PurchaseItem.quantity > PurchaseItem.quantity_received, )

    @property
    def purchase_item(self):
        return PurchaseItem.get(self.id, store=self.store)


class ConsignedItemAndStockView(PurchasedItemAndStockView):
    columns = PurchasedItemAndStockView.columns.copy()
    columns.update(dict(
        sold=PurchaseItem.quantity_sold,
        returned=PurchaseItem.quantity_returned,
    ))
    clause = And(PurchaseOrder.consigned == True,
                 PurchaseOrder.branch_id == ProductStockItem.branch_id)


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
    _Responsible = ClassAlias(Person, "responsible")
    _Supplier = ClassAlias(Person, "supplier_person")
    _PurchaseUser = ClassAlias(LoginUser, "purchase_user")
    _PurchaseResponsible = ClassAlias(Person, "purchase_responsible")

    columns = dict(
        id=ReceivingOrder.id,
        receival_date=ReceivingOrder.receival_date,
        invoice_number=ReceivingOrder.invoice_number,
        invoice_total=ReceivingOrder.invoice_total,
        purchase_identifier=PurchaseOrder.identifier,
        branch_id=ReceivingOrder.branch_id,
        purchase_responsible_name=_PurchaseResponsible.name,
        responsible_name=_Responsible.name,
        supplier_name=_Supplier.name,
        )

    joins = [
        LeftJoin(PurchaseOrder,
                   ReceivingOrder.purchase_id == PurchaseOrder.id),
        LeftJoin(_PurchaseUser,
                   PurchaseOrder.responsible_id == _PurchaseUser.id),
        LeftJoin(_PurchaseResponsible,
                   _PurchaseUser.person_id == _PurchaseResponsible.id),
        LeftJoin(Supplier,
                   ReceivingOrder.supplier_id == Supplier.id),
        LeftJoin(_Supplier,
                   Supplier.person_id == _Supplier.id),
        LeftJoin(LoginUser,
                   ReceivingOrder.responsible_id == LoginUser.id),
        LeftJoin(_Responsible,
                   LoginUser.person_id == _Responsible.id),
    ]


class SaleItemsView(Viewable):
    """Show information about sold items and about the corresponding sale.
    This is slightlig difrent than SoldItemView that groups sold items from
    diferent sales.
    """

    columns = dict(
        id=SaleItem.id,
        sellable_id=Sellable.id,
        code=Sellable.code,
        description=Sellable.description,
        sale_id=SaleItem.sale_id,
        sale_identifier=Sale.identifier,
        sale_date=Sale.open_date,
        client_name=Person.name,
        quantity=SaleItem.quantity,
        unit_description=SellableUnit.description,
    )

    joins = [
        LeftJoin(Sellable,
                    Sellable.id == SaleItem.sellable_id),
        LeftJoin(Sale,
                   SaleItem.sale_id == Sale.id),
        LeftJoin(SellableUnit,
                   Sellable.unit_id == SellableUnit.id),
        LeftJoin(Client,
                   Sale.client_id == Client.id),
        LeftJoin(Person,
                   Client.person_id == Person.id),
    ]

    clause = Or(Sale.status == Sale.STATUS_CONFIRMED,
                Sale.status == Sale.STATUS_PAID,
                Sale.status == Sale.STATUS_RENEGOTIATED,
                Sale.status == Sale.STATUS_ORDERED)


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
        id=ReceivingOrderItem.id,
        order_identifier=ReceivingOrder.identifier,
        purchase_identifier=PurchaseOrder.identifier,
        purchase_item_id=ReceivingOrderItem.purchase_item_id,
        sellable_id=ReceivingOrderItem.sellable_id,
        invoice_number=ReceivingOrder.invoice_number,
        receival_date=ReceivingOrder.receival_date,
        quantity=ReceivingOrderItem.quantity,
        cost=ReceivingOrderItem.cost,
        unit_description=SellableUnit.description,
        supplier_name=Person.name,
    )

    joins = [
        LeftJoin(ReceivingOrder,
                   ReceivingOrderItem.receiving_order_id == ReceivingOrder.id),
        LeftJoin(PurchaseOrder,
                   ReceivingOrder.purchase_id == PurchaseOrder.id),
        LeftJoin(Sellable,
                   ReceivingOrderItem.sellable_id == Sellable.id),
        LeftJoin(SellableUnit,
                   Sellable.unit_id == SellableUnit.id),
        LeftJoin(Supplier,
                   ReceivingOrder.supplier_id == Supplier.id),
        LeftJoin(Person,
                   Supplier.person_id == Person.id),
    ]


class ProductionItemView(Viewable):
    columns = dict(id=ProductionItem.id,
                   order_identifier=ProductionOrder.identifier,
                   order_status=ProductionOrder.status,
                   quantity=ProductionItem.quantity,
                   produced=ProductionItem.produced,
                   lost=ProductionItem.lost,
                   category_description=SellableCategory.description,
                   unit_description=SellableUnit.description,
                   description=Sellable.description, )

    joins = [
        LeftJoin(ProductionOrder,
                   ProductionItem.order_id == ProductionOrder.id),
        LeftJoin(Product,
                   ProductionItem.product_id == Product.id),
        LeftJoin(Sellable,
                    Sellable.id == Product.sellable_id),
        LeftJoin(SellableCategory,
                   SellableCategory.id == Sellable.category_id),
        LeftJoin(SellableUnit,
                   Sellable.unit_id == SellableUnit.id),
    ]

    @property
    def production_item(self):
        return ProductionItem.get(self.id, store=self.store)


class LoanView(Viewable):
    PersonBranch = ClassAlias(Person, 'person_branch')
    PersonResponsible = ClassAlias(Person, 'person_responsible')
    PersonClient = ClassAlias(Person, 'person_client')

    columns = dict(
        id=Loan.id,
        identifier=Loan.identifier,
        status=Loan.status,
        open_date=Loan.open_date,
        close_date=Loan.close_date,
        expire_date=Loan.expire_date,

        removed_by=Loan.removed_by,
        branch_name=PersonBranch.name,
        responsible_name=PersonResponsible.name,
        client_name=PersonClient.name,
        loaned=Sum(LoanItem.quantity),
        total=Sum(LoanItem.quantity * LoanItem.price),
    )
    joins = [
        Join(LoanItem, Loan.id == LoanItem.loan_id),
        LeftJoin(Branch,
                   Loan.branch_id == Branch.id),
        LeftJoin(LoginUser,
                   Loan.responsible_id == LoginUser.id),
        LeftJoin(Client,
                   Loan.client_id == Client.id),

        LeftJoin(PersonBranch,
                   Branch.person_id == PersonBranch.id),
        LeftJoin(PersonResponsible,
                   LoginUser.person_id == PersonResponsible.id),
        LeftJoin(PersonClient,
                   Client.person_id == PersonClient.id),
    ]

    @property
    def loan(self):
        return Loan.get(self.id, store=self.store)


class LoanItemView(Viewable):
    columns = dict(
        id=LoanItem.id,
        loan_identifier=Loan.identifier,
        loan_status=Loan.status,
        opened=Loan.open_date,
        closed=Loan.close_date,
        quantity=LoanItem.quantity,
        sale_quantity=LoanItem.sale_quantity,
        return_quantity=LoanItem.return_quantity,
        price=LoanItem.price,
        total=LoanItem.quantity * LoanItem.price,
        sellable_id=Sellable.id,
        code=Sellable.code,
        category_description=SellableCategory.description,
        unit_description=SellableUnit.description,
        description=Sellable.description,
    )

    joins = [
        LeftJoin(Loan, LoanItem.loan_id == Loan.id),
        LeftJoin(Sellable,
                   LoanItem.sellable_id == Sellable.id),
        LeftJoin(SellableUnit,
                   Sellable.unit_id == SellableUnit.id),
        LeftJoin(SellableCategory,
                   SellableCategory.id == Sellable.category_id),
    ]


class AccountView(Viewable):

    class _SourceSum(Viewable):
        columns = dict(
            id=AccountTransaction.source_account_id,
            value=Sum(AccountTransaction.value),
            )

    class _DestSum(Viewable):
        columns = dict(
            id=AccountTransaction.account_id,
            value=Sum(AccountTransaction.value),
            )

    columns = dict(
        id=Account.id,
        parent_id=Account.parent_id,
        account_type=Account.account_type,
        dest_account_id=Account.parent_id,
        description=Account.description,
        code=Account.code,
        source_value=Field('source_sum', 'value'),
        dest_value=Field('dest_sum', 'value'),
        )

    joins = [
        LeftJoin(ViewableAlias(_SourceSum, 'source_sum'),
                   Field('source_sum', 'id') == Account.id),
        LeftJoin(ViewableAlias(_DestSum, 'dest_sum'),
                   Field('dest_sum', 'id') == Account.id),
        ]

    @property
    def account(self):
        """Get the account for this view"""
        return Account.get(self.id, store=self.store)

    @property
    def parent_account(self):
        """Get the parent account for this view"""
        return Account.get(self.parent_id, store=self.store)

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
    PersonTransporter = ClassAlias(Person, 'person_transporter')
    PersonClient = ClassAlias(Person, 'person_client')

    columns = dict(
        # Delivery
        id=Delivery.id,
        status=Delivery.status,
        tracking_code=Delivery.tracking_code,
        open_date=Delivery.open_date,
        deliver_date=Delivery.deliver_date,
        receive_date=Delivery.receive_date,

        # Transporter
        transporter_name=PersonTransporter.name,

        # Client
        client_name=PersonClient.name,

        # Sale
        sale_identifier=Sale.identifier,

        # Address
        address_id=Delivery.address_id,
    )

    joins = [
        LeftJoin(Transporter,
                 Transporter.id == Delivery.transporter_id),
        LeftJoin(PersonTransporter,
                 PersonTransporter.id == Transporter.person_id),
        LeftJoin(SaleItem,
                 SaleItem.id == Delivery.service_item_id),
        LeftJoin(Sale,
                 Sale.id == SaleItem.sale_id),
        LeftJoin(Client,
                 Client.id == Sale.client_id),
        LeftJoin(PersonClient,
                 PersonClient.id == Client.person_id),
        #LeftJoin(Address,
        #         Address.person_id == Client.person_id),
        ]

    @property
    def status_str(self):
        return Delivery.statuses[self.status]

    @property
    def delivery(self):
        return Delivery.get(self.id, store=self.store)

    @property
    def address_str(self):
        return Address.get(self.address_id,
               store=self.store).get_description()
