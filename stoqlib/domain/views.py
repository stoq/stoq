# Mode: Python; coding: utf-8 -*-
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

from kiwi.currency import currency
from storm.expr import (And, Coalesce, Eq, Join, LeftJoin, Or, Sum, Select,
                        Alias, Count, Cast)
from storm.info import ClassAlias

from stoqlib.database.expr import Date, Distinct, Field
from stoqlib.database.viewable import Viewable
from stoqlib.domain.account import Account, AccountTransaction
from stoqlib.domain.address import Address
from stoqlib.domain.commission import CommissionSource
from stoqlib.domain.costcenter import CostCenterEntry
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
                                    ProductSupplierInfo,
                                    StockTransactionHistory,
                                    Storable)
from stoqlib.domain.production import ProductionOrder, ProductionItem
from stoqlib.domain.purchase import (Quotation, QuoteGroup, PurchaseOrder,
                                     PurchaseItem)
from stoqlib.domain.receiving import ReceivingOrderItem, ReceivingOrder
from stoqlib.domain.sale import SaleItem, Sale, Delivery
from stoqlib.domain.returnedsale import ReturnedSale
from stoqlib.domain.sellable import (Sellable, SellableUnit,
                                     SellableCategory,
                                     SellableTaxConstant)
from stoqlib.domain.stockdecrease import (StockDecrease, StockDecreaseItem)
from stoqlib.lib.decorators import cached_property
from stoqlib.lib.dateutils import localnow
from stoqlib.lib.validators import is_date_in_interval


# Use a subselect to count the number of items, because that takes a lot less
# time (since it doesn't have a huge GROUP BY clause).
# Note that there are two subselects possible. The first should be used when the
# viewable is queried without the branch and the second when it is queried with
# the branch.
_StockSummary = Alias(Select(
    columns=[ProductStockItem.storable_id,
             Alias(Sum(ProductStockItem.quantity), 'stock'),
             Alias(Sum(ProductStockItem.quantity *
                       ProductStockItem.stock_cost), 'total_stock_cost')],
    tables=[ProductStockItem],
    group_by=[ProductStockItem.storable_id]), '_stock_summary')

_StockBranchSummary = Alias(
    Select(columns=_StockSummary.expr.columns + [ProductStockItem.branch_id],
           tables=_StockSummary.expr.tables[:],
           group_by=_StockSummary.expr.group_by + [
               ProductStockItem.branch_id]),
    '_stock_summary')


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

    sellable = Sellable
    product = Product

    # Sellable
    id = Sellable.id
    code = Sellable.code
    barcode = Sellable.barcode
    status = Sellable.status
    cost = Sellable.cost
    description = Sellable.description
    image_id = Sellable.image_id
    base_price = Sellable.base_price
    on_sale_price = Sellable.on_sale_price
    on_sale_start_date = Sellable.on_sale_start_date
    on_sale_end_date = Sellable.on_sale_end_date

    # Product
    product_id = Product.id
    location = Product.location
    model = Product.model

    manufacturer = ProductManufacturer.name
    tax_description = SellableTaxConstant.description
    category_description = SellableCategory.description
    unit = SellableUnit.description

    # Aggregates
    total_stock_cost = Coalesce(Field('_stock_summary', 'total_stock_cost'), 0)
    stock = Coalesce(Field('_stock_summary', 'stock'), 0)

    tables = [
        # Keep this first 4 joins in this order, so find_by_branch may change it.
        Sellable,
        Join(Product, Product.sellable_id == Sellable.id),
        LeftJoin(Storable, Storable.product_id == Product.id),
        LeftJoin(_StockSummary,
                 Field('_stock_summary', 'storable_id') == Storable.id),

        LeftJoin(SellableTaxConstant,
                 SellableTaxConstant.id == Sellable.tax_constant_id),
        LeftJoin(SellableCategory, SellableCategory.id == Sellable.category_id),
        LeftJoin(SellableUnit, Sellable.unit_id == SellableUnit.id),
        LeftJoin(ProductManufacturer,
                 Product.manufacturer_id == ProductManufacturer.id),
    ]

    clause = Sellable.status != Sellable.STATUS_CLOSED

    @classmethod
    def post_search_callback(cls, sresults):
        select = sresults.get_select_expr(Count(Distinct(Sellable.id)),
                                          Sum(Field('_stock_summary', 'stock')))
        return ('count', 'sum'), select

    @classmethod
    def find_by_branch(cls, store, branch):
        if branch is None:
            return store.find(cls)

        # When we need to filter on the branch, we also need to add the branch
        # column on the ProductStockItem subselect, so the filter works. We cant
        # keep the branch_id on the main subselect, since that will cause the
        # results to be duplicate when not filtering by branch (probably the
        # most common case). So, we need all of this workaround

        # Make sure that the join we are replacing is the correct one.
        assert cls.tables[3].right == _StockSummary

        # Highjack the class being queried, since we need to add the branch
        # on the ProductStockItem subselect to filter it later
        class HighjackedViewable(cls):
            tables = cls.tables[:]
            tables[3] = LeftJoin(_StockBranchSummary,
                                 Field('_stock_summary',
                                       'storable_id') == Storable.id)

        # Also show products that were never purchased.
        query = Or(Field('_stock_summary', 'branch_id') == branch.id,
                   Eq(Field('_stock_summary', 'branch_id'), None))

        return store.find(HighjackedViewable, query)

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
    def stock_cost(self):
        if self.stock:
            return self.total_stock_cost / self.stock

        return 0

    @property
    def price(self):
        # See Sellable.price property
        if self.on_sale_price:
            today = localnow()
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

    tables = ProductFullStockView.tables[:]
    tables.extend([
        Join(ProductComponent, ProductComponent.product_id == Product.id),
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
        ProductFullStockView.stock >= 0,
    )


class ProductWithStockBranchView(ProductWithStockView):
    """The same as ProductWithStockView but has a branch_id property that must
    be used to filte.

    Note that when using this viewable, all queries must include the branch
    filter, otherwise, the results may be duplicated (once for each branch in
    the database)
    """
    minimum_quantity = Storable.minimum_quantity
    maximum_quantity = Storable.maximum_quantity
    branch_id = Field('_stock_summary', 'branch_id')
    storable_id = Field('_stock_summary', 'storable_id')

    tables = ProductWithStockView.tables[:]
    tables[3] = LeftJoin(_StockBranchSummary, storable_id == Storable.id)


# This subselect should query only from PurchaseItem, otherwise, more one
# product may appear more than once in the results (if there are purchase
# orders for it)
_PurchaseItemTotal = Select(
    columns=[PurchaseItem.sellable_id,
             Alias(Sum(PurchaseItem.quantity -
                       PurchaseItem.quantity_received),
                   'to_receive')],
    tables=[PurchaseItem,
            LeftJoin(PurchaseOrder, PurchaseOrder.id == PurchaseItem.order_id)],
    where=PurchaseOrder.status == PurchaseOrder.ORDER_CONFIRMED,
    group_by=[PurchaseItem.sellable_id])


class ProductFullStockItemView(ProductFullStockView):
    # ProductFullStockView already joins with a 1 to Many table (Sellable
    # with ProductStockItem).
    #
    # This is why we must join PurchaseItem (another 1 to many table) in a
    # subquery

    minimum_quantity = Storable.minimum_quantity
    maximum_quantity = Storable.maximum_quantity
    to_receive_quantity = Coalesce(Field('_purchase_total', 'to_receive'), 0)

    difference = ProductFullStockView.stock - Storable.minimum_quantity

    tables = ProductFullStockView.tables[:]
    tables.append(LeftJoin(Alias(_PurchaseItemTotal, '_purchase_total'),
                           Field('_purchase_total',
                                 'sellable_id') == Sellable.id))


class ProductFullStockItemSupplierView(ProductFullStockItemView):
    """ Just like ProductFullStockView, but will also be joined with
    ProductSupplierInfo and Supplier, so use this only if you are specifing a
    supplier in the query.
    """

    tables = ProductFullStockItemView.tables[:]
    tables.extend([
        Join(ProductSupplierInfo, Product.id == ProductSupplierInfo.product_id),
        Join(Supplier, Supplier.id == ProductSupplierInfo.supplier_id),
    ])


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

    id = ProductHistory.sellable_id
    branch = ProductHistory.branch_id

    sold_date = ProductHistory.sold_date
    received_date = ProductHistory.received_date
    production_date = ProductHistory.production_date
    decreased_date = ProductHistory.decreased_date

    code = Sellable.code
    description = Sellable.description

    # Aggregates
    quantity_sold = Sum(ProductHistory.quantity_sold)
    quantity_received = Sum(ProductHistory.quantity_received)
    quantity_transfered = Sum(ProductHistory.quantity_transfered)
    quantity_produced = Sum(ProductHistory.quantity_produced)
    quantity_consumed = Sum(ProductHistory.quantity_consumed)
    quantity_lost = Sum(ProductHistory.quantity_lost)
    quantity_decreased = Sum(ProductHistory.quantity_decreased)

    tables = [
        ProductHistory,
        Join(Sellable, ProductHistory.sellable_id == Sellable.id),
    ]

    # This are columns that are not supposed to be queried, but should still be
    # able to be filtered
    hidden_columns = ['sold_date', 'received_date', 'production_date',
                      'decreased_date']

    group_by = [id, branch, code, description]


class ProductBranchStockView(Viewable):
    """Stores information about the stock of a certain |product| among
    all branches
    """
    branch = Branch

    id = Branch.id
    branch_name = Person.name
    storable_id = ProductStockItem.storable_id
    stock = ProductStockItem.quantity

    tables = [
        Branch,
        Join(Person, Person.id == Branch.person_id),
        Join(ProductStockItem, ProductStockItem.branch_id == Branch.id),
    ]

    @classmethod
    def find_by_storable(cls, store, storable):
        return store.find(cls, storable_id=storable.id)


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

    sellable = Sellable
    product = Product

    id = Sellable.id
    code = Sellable.code
    barcode = Sellable.barcode
    status = Sellable.status
    cost = Sellable.cost
    description = Sellable.description
    on_sale_price = Sellable.on_sale_price
    on_sale_start_date = Sellable.on_sale_start_date
    on_sale_end_date = Sellable.on_sale_end_date
    base_price = Sellable.base_price
    max_discount = Sellable.max_discount

    product_id = Product.id
    model = Product.model

    unit = SellableUnit.description
    manufacturer = ProductManufacturer.name
    category_description = SellableCategory.description

    # Aggregates
    stock = Coalesce(Sum(ProductStockItem.quantity), 0)

    tables = [
        Sellable,
        LeftJoin(SellableUnit, SellableUnit.id == Sellable.unit_id),
        LeftJoin(SellableCategory, SellableCategory.id == Sellable.category_id),
        LeftJoin(Product, Product.sellable_id == Sellable.id),
        LeftJoin(Storable, Storable.product_id == Product.id),
        LeftJoin(ProductStockItem, ProductStockItem.storable_id == Storable.id),
        LeftJoin(ProductManufacturer,
                 Product.manufacturer_id == ProductManufacturer.id),
    ]

    group_by = [Sellable, SellableUnit, product_id, model, unit,
                manufacturer, category_description]

    @classmethod
    def find_by_branch(cls, store, branch):
        if branch:
            # We need the OR part to be able to list services
            query = Or(ProductStockItem.branch == branch,
                       Eq(ProductStockItem.branch_id, None))
            return store.find(cls, query)

        return store.find(cls)

    @property
    def price(self):
        # See Sellable.price property
        if self.on_sale_price:
            today = localnow()
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

    category = SellableCategory

    id = SellableCategory.id
    parent_id = SellableCategory.category_id
    description = SellableCategory.description
    suggested_markup = SellableCategory.suggested_markup

    commission = CommissionSource.direct_value
    installments_commission = CommissionSource.installments_value

    tables = [
        SellableCategory,
        LeftJoin(CommissionSource,
                 CommissionSource.category_id == SellableCategory.id),
    ]

    def get_parent(self):
        if not self.parent_id:
            return None

        return self.store.find(SellableCategoryView, id=self.parent_id).one()

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

    group = QuoteGroup
    quotation = Quotation
    purchase = PurchaseOrder

    id = Quotation.id
    purchase_id = Quotation.purchase_id
    group_id = Quotation.group_id
    identifier = Quotation.identifier
    identifier_str = Cast(Quotation.identifier, 'text')
    group_identifier = QuoteGroup.identifier
    open_date = PurchaseOrder.open_date
    deadline = PurchaseOrder.quote_deadline
    supplier_name = Person.name

    tables = [
        Quotation,
        Join(QuoteGroup,
             QuoteGroup.id == Quotation.group_id),
        LeftJoin(PurchaseOrder,
                 PurchaseOrder.id == Quotation.purchase_id),
        LeftJoin(Supplier,
                 Supplier.id == PurchaseOrder.supplier_id),
        LeftJoin(Person, Person.id == Supplier.person_id),
    ]


class SoldItemView(Viewable):
    """Stores information about all sale items, including the average cost
    of the sold items.
    """

    id = Sellable.id
    code = Sellable.code
    description = Sellable.description
    category = SellableCategory.description

    # Aggregate
    quantity = Sum(SaleItem.quantity)
    total_cost = Sum(SaleItem.quantity * SaleItem.average_cost)

    tables = [
        Sellable,
        LeftJoin(SaleItem, Sellable.id == SaleItem.sellable_id),
        LeftJoin(Sale, SaleItem.sale_id == Sale.id),
        LeftJoin(SellableCategory, Sellable.category_id == SellableCategory.id),
    ]

    clause = Or(Sale.status == Sale.STATUS_CONFIRMED,
                Sale.status == Sale.STATUS_PAID,
                Sale.status == Sale.STATUS_ORDERED)

    group_by = [id, code, description, category, Sale.status]

    @classmethod
    def find_by_branch_date(cls, store, branch, date):
        queries = []
        if branch:
            queries.append(Sale.branch == branch)

        if date:
            if isinstance(date, tuple):
                date_query = And(Date(Sale.confirm_date) >= date[0],
                                 Date(Sale.confirm_date) <= date[1])
            else:
                date_query = Date(Sale.confirm_date) == date

            queries.append(date_query)

        if queries:
            return store.find(cls, And(*queries))
        return store.find(cls)

    @property
    def average_cost(self):
        if self.quantity:
            return self.total_cost / self.quantity
        return 0


class StockDecreaseView(Viewable):
    """Stores information about all stock decreases
    """
    _PersonBranch = ClassAlias(Person, "person_branch")

    id = StockDecrease.id
    identifier = StockDecrease.identifier
    confirm_date = StockDecrease.confirm_date

    branch_name = _PersonBranch.name
    removed_by_name = Person.name

    tables = [
        StockDecrease,
        Join(Employee, StockDecrease.removed_by_id == Employee.id),
        Join(Person, Employee.person_id == Person.id),
        Join(Branch, StockDecrease.branch_id == Branch.id),
        Join(_PersonBranch, Branch.person_id == _PersonBranch.id),
    ]


class StockDecreaseItemsView(Viewable):
    """Stores information about all stock decrease items
    """
    id = StockDecreaseItem.id
    quantity = StockDecreaseItem.quantity
    sellable = StockDecreaseItem.sellable_id
    decrease_id = StockDecrease.id
    decrease_identifier = StockDecrease.identifier
    date = StockDecrease.confirm_date
    removed_by_name = Person.name
    unit_description = SellableUnit.description

    tables = [
        StockDecreaseItem,
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

    branch_name = Person.name

    # Aggregates
    total = Sum(SaleItem.quantity * SaleItem.price)

    tables = SoldItemView.tables[:]
    tables.extend([
        LeftJoin(Branch, Branch.id == Sale.branch_id),
        LeftJoin(Person, Branch.person_id == Person.id)])

    clause = Or(SoldItemView.clause,
                Sale.status == Sale.STATUS_RENEGOTIATED)

    group_by = SoldItemView.group_by[:]
    group_by.append(branch_name)


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

    purchase_item = PurchaseItem

    id = PurchaseItem.id
    purchased = PurchaseItem.quantity
    received = PurchaseItem.quantity_received
    expected_receival_date = PurchaseItem.expected_receival_date

    order_identifier = PurchaseOrder.identifier
    order_identifier_str = Cast(PurchaseOrder.identifier, 'text')
    purchased_date = PurchaseOrder.open_date
    branch = PurchaseOrder.branch_id

    code = Sellable.code
    description = Sellable.description

    product_id = Product.id

    # Aggregate
    stocked = Sum(ProductStockItem.quantity)

    tables = [
        PurchaseItem,
        LeftJoin(PurchaseOrder, PurchaseItem.order_id == PurchaseOrder.id),
        LeftJoin(Sellable, Sellable.id == PurchaseItem.sellable_id),
        LeftJoin(Product, Product.sellable_id == PurchaseItem.sellable_id),
        LeftJoin(Storable, Storable.product_id == Product.id),
        LeftJoin(ProductStockItem, ProductStockItem.storable_id == Storable.id),
    ]

    clause = And(PurchaseOrder.status == PurchaseOrder.ORDER_CONFIRMED,
                 PurchaseOrder.branch_id == ProductStockItem.branch_id,
                 PurchaseItem.quantity > PurchaseItem.quantity_received, )

    group_by = [PurchaseItem, order_identifier, purchased_date, branch, code,
                description, product_id]


class ConsignedItemAndStockView(PurchasedItemAndStockView):
    sold = PurchaseItem.quantity_sold
    returned = PurchaseItem.quantity_returned

    clause = And(Eq(PurchaseOrder.consigned, True),
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

    order = ReceivingOrder

    id = ReceivingOrder.id
    receival_date = ReceivingOrder.receival_date
    invoice_number = ReceivingOrder.invoice_number
    invoice_total = ReceivingOrder.invoice_total
    purchase_identifier = PurchaseOrder.identifier
    purchase_identifier_str = Cast(PurchaseOrder.identifier, 'text')
    branch_id = ReceivingOrder.branch_id
    purchase_responsible_name = _PurchaseResponsible.name
    responsible_name = _Responsible.name
    supplier_name = _Supplier.name

    tables = [
        ReceivingOrder,
        LeftJoin(PurchaseOrder, ReceivingOrder.purchase_id == PurchaseOrder.id),
        LeftJoin(_PurchaseUser,
                 PurchaseOrder.responsible_id == _PurchaseUser.id),
        LeftJoin(_PurchaseResponsible,
                 _PurchaseUser.person_id == _PurchaseResponsible.id),
        LeftJoin(Supplier, ReceivingOrder.supplier_id == Supplier.id),
        LeftJoin(_Supplier, Supplier.person_id == _Supplier.id),
        LeftJoin(LoginUser, ReceivingOrder.responsible_id == LoginUser.id),
        LeftJoin(_Responsible, LoginUser.person_id == _Responsible.id),
    ]


class SaleItemsView(Viewable):
    """Show information about sold items and about the corresponding sale.
    This is slightlig difrent than SoldItemView that groups sold items from
    diferent sales.
    """

    id = SaleItem.id
    sellable_id = Sellable.id
    code = Sellable.code
    description = Sellable.description
    sale_id = SaleItem.sale_id
    sale_identifier = Sale.identifier
    sale_date = Sale.open_date
    client_name = Person.name
    quantity = SaleItem.quantity
    unit_description = SellableUnit.description

    tables = [
        SaleItem,
        LeftJoin(Sellable, Sellable.id == SaleItem.sellable_id),
        LeftJoin(Sale, SaleItem.sale_id == Sale.id),
        LeftJoin(SellableUnit, Sellable.unit_id == SellableUnit.id),
        LeftJoin(Client, Sale.client_id == Client.id),
        LeftJoin(Person, Client.person_id == Person.id),
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

    id = ReceivingOrderItem.id
    order_identifier = ReceivingOrder.identifier
    purchase_identifier = PurchaseOrder.identifier
    purchase_item_id = ReceivingOrderItem.purchase_item_id
    sellable_id = ReceivingOrderItem.sellable_id
    invoice_number = ReceivingOrder.invoice_number
    receival_date = ReceivingOrder.receival_date
    quantity = ReceivingOrderItem.quantity
    cost = ReceivingOrderItem.cost
    unit_description = SellableUnit.description
    supplier_name = Person.name

    tables = [
        ReceivingOrderItem,
        LeftJoin(ReceivingOrder,
                 ReceivingOrderItem.receiving_order_id == ReceivingOrder.id),
        LeftJoin(PurchaseOrder, ReceivingOrder.purchase_id == PurchaseOrder.id),
        LeftJoin(Sellable, ReceivingOrderItem.sellable_id == Sellable.id),
        LeftJoin(SellableUnit, Sellable.unit_id == SellableUnit.id),
        LeftJoin(Supplier, ReceivingOrder.supplier_id == Supplier.id),
        LeftJoin(Person, Supplier.person_id == Person.id),
    ]


class ProductionItemView(Viewable):
    production_item = ProductionItem

    id = ProductionItem.id
    order_identifier = ProductionOrder.identifier
    order_identifier_str = Cast(ProductionOrder.identifier, 'text')
    order_status = ProductionOrder.status
    quantity = ProductionItem.quantity
    produced = ProductionItem.produced
    lost = ProductionItem.lost
    category_description = SellableCategory.description
    unit_description = SellableUnit.description
    description = Sellable.description

    tables = [
        ProductionItem,
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


class ProductBrandStockView(Viewable):
    # Alias of Branch to Person table

    id = Product.brand
    brand = Coalesce(Product.brand, u'')

    quantity = Sum(ProductStockItem.quantity)

    tables = [
        Product,
        LeftJoin(Storable,
                 Storable.product_id == Product.id),
        LeftJoin(ProductStockItem,
                 ProductStockItem.storable_id == Storable.id),
        LeftJoin(Branch, Branch.id == ProductStockItem.branch_id)
    ]
    group_by = [id, brand]

    @classmethod
    def find_by_branch(cls, store, branch):
        if branch:
            return store.find(cls, ProductStockItem.branch_id == branch.id)

        return store.find(cls)


class ReturnedSalesView(Viewable):
    PersonBranch = ClassAlias(Person, 'person_branch')
    PersonResponsible = ClassAlias(Person, 'responsible_sale')
    PersonClient = ClassAlias(Person, 'person_client')

    returned_sale = ReturnedSale

    id = ReturnedSale.id
    identifier = ReturnedSale.identifier
    identifier_str = Cast(ReturnedSale.identifier, 'text')
    return_date = ReturnedSale.return_date
    reason = ReturnedSale.reason
    invoice_number = ReturnedSale.invoice_number

    sale_id = Sale.id
    sale_identifier = Sale.identifier
    sale_identifier_str = Cast(Sale.identifier, 'text')

    responsible_name = PersonResponsible.name
    branch_name = PersonBranch.name
    client_name = PersonClient.name

    tables = [
        ReturnedSale,
        Join(Sale, Sale.id == ReturnedSale.sale_id),
        Join(LoginUser, LoginUser.id == ReturnedSale.responsible_id),
        Join(PersonResponsible, PersonResponsible.id == LoginUser.person_id),
        Join(Branch, Branch.id == ReturnedSale.branch_id),
        Join(PersonBranch, PersonBranch.id == Branch.person_id),
        LeftJoin(Client, Client.id == Sale.client_id),
        LeftJoin(PersonClient, PersonClient.id == Client.person_id),
    ]


class LoanView(Viewable):
    PersonBranch = ClassAlias(Person, 'person_branch')
    PersonResponsible = ClassAlias(Person, 'person_responsible')
    PersonClient = ClassAlias(Person, 'person_client')

    loan = Loan

    id = Loan.id
    identifier = Loan.identifier
    identifier_str = Cast(Loan.identifier, 'text')
    status = Loan.status
    open_date = Loan.open_date
    close_date = Loan.close_date
    expire_date = Loan.expire_date
    removed_by = Loan.removed_by
    client_id = Loan.client_id
    branch_id = Loan.branch_id

    branch_name = PersonBranch.name
    responsible_name = PersonResponsible.name
    client_name = PersonClient.name

    # Aggregates
    loaned = Sum(LoanItem.quantity)
    total = Sum(LoanItem.quantity * LoanItem.price)

    tables = [
        Loan,
        Join(LoanItem, Loan.id == LoanItem.loan_id),
        LeftJoin(Branch, Loan.branch_id == Branch.id),
        LeftJoin(LoginUser, Loan.responsible_id == LoginUser.id),
        LeftJoin(Client, Loan.client_id == Client.id),
        LeftJoin(PersonBranch, Branch.person_id == PersonBranch.id),
        LeftJoin(PersonResponsible,
                 LoginUser.person_id == PersonResponsible.id),
        LeftJoin(PersonClient, Client.person_id == PersonClient.id),
    ]

    group_by = [Loan, branch_name, responsible_name, client_name]


class LoanItemView(Viewable):
    id = LoanItem.id
    quantity = LoanItem.quantity
    sale_quantity = LoanItem.sale_quantity
    return_quantity = LoanItem.return_quantity
    price = LoanItem.price
    total = LoanItem.quantity * LoanItem.price

    loan_identifier = Loan.identifier
    loan_status = Loan.status
    opened = Loan.open_date
    closed = Loan.close_date

    sellable_id = Sellable.id
    code = Sellable.code
    description = Sellable.description

    category_description = SellableCategory.description
    unit_description = SellableUnit.description

    identifier_str = Cast(Loan.identifier, 'text')

    tables = [
        LoanItem,
        LeftJoin(Loan, LoanItem.loan_id == Loan.id),
        LeftJoin(Sellable, LoanItem.sellable_id == Sellable.id),
        LeftJoin(SellableUnit, Sellable.unit_id == SellableUnit.id),
        LeftJoin(SellableCategory, SellableCategory.id == Sellable.category_id),
    ]


_SourceSum = Select(
    columns=[AccountTransaction.source_account_id,
             Alias(Sum(AccountTransaction.value), 'value')],
    tables=[AccountTransaction],
    group_by=[AccountTransaction.source_account_id])

_DestSum = Select(
    columns=[AccountTransaction.account_id,
             Alias(Sum(AccountTransaction.value), 'value')],
    tables=[AccountTransaction],
    group_by=[AccountTransaction.account_id])


class AccountView(Viewable):

    account = Account

    id = Account.id
    parent_id = Account.parent_id
    account_type = Account.account_type
    dest_account_id = Account.parent_id
    description = Account.description
    code = Account.code

    source_value = Field('source_sum', 'value')
    dest_value = Field('dest_sum', 'value')

    tables = [
        Account,
        LeftJoin(Alias(_SourceSum, 'source_sum'),
                 Field('source_sum', 'source_account_id') == Account.id),
        LeftJoin(Alias(_DestSum, 'dest_sum'),
                 Field('dest_sum', 'account_id') == Account.id),
    ]

    @property
    def parent_account(self):
        """Get the parent account for this view"""
        return self.store.get(Account, self.parent_id)

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

    delivery = Delivery

    # Delivery
    id = Delivery.id
    status = Delivery.status
    tracking_code = Delivery.tracking_code
    open_date = Delivery.open_date
    deliver_date = Delivery.deliver_date
    receive_date = Delivery.receive_date

    identifier_str = Cast(Sale.identifier, 'text')

    # Transporter
    transporter_name = PersonTransporter.name

    # Client
    client_name = PersonClient.name

    # Sale
    sale_identifier = Sale.identifier

    # Address
    address_id = Delivery.address_id

    tables = [
        Delivery,
        LeftJoin(Transporter, Transporter.id == Delivery.transporter_id),
        LeftJoin(PersonTransporter,
                 PersonTransporter.id == Transporter.person_id),
        LeftJoin(SaleItem, SaleItem.id == Delivery.service_item_id),
        LeftJoin(Sale, Sale.id == SaleItem.sale_id),
        LeftJoin(Client, Client.id == Sale.client_id),
        LeftJoin(PersonClient, PersonClient.id == Client.person_id),
        # LeftJoin(Address,
        #         Address.person_id == Client.person_id),
    ]

    @property
    def status_str(self):
        return Delivery.statuses[self.status]

    @property
    def address_str(self):
        return self.store.get(Address, self.address_id).get_description()


class CostCenterEntryStockView(Viewable):
    """A viewable with information about cost center entries related to stock
    transactions.
    """

    stock_transaction = StockTransactionHistory

    # StockTransactionHistory has an indirect reference to only one of this
    # (sale_item or stock_decrease_item), but here we are speculatively quering
    # both to cache the results, avoiding extra queries when getting the
    # description of the transaction
    _sale_item = SaleItem
    _stock_decrease_item = StockDecreaseItem
    _sale = Sale
    _stock_decrease = StockDecrease

    id = CostCenterEntry.id
    cost_center_id = CostCenterEntry.cost_center_id

    date = StockTransactionHistory.date
    stock_cost = StockTransactionHistory.stock_cost
    quantity = StockTransactionHistory.quantity

    responsible_name = Person.name

    sellable_id = Sellable.id
    code = Sellable.code
    product_description = Sellable.description

    tables = [
        CostCenterEntry,
        Join(StockTransactionHistory,
             CostCenterEntry.stock_transaction_id == StockTransactionHistory.id),
        Join(LoginUser, StockTransactionHistory.responsible_id == LoginUser.id),
        Join(Person, LoginUser.person_id == Person.id),
        Join(ProductStockItem,
             StockTransactionHistory.product_stock_item_id == ProductStockItem.id),
        Join(Storable, ProductStockItem.storable_id == Storable.id),
        Join(Product, Storable.product_id == Product.id),
        Join(Sellable, Product.sellable_id == Sellable.id),

        # possible sale item and stock decrease item
        LeftJoin(SaleItem, SaleItem.id == StockTransactionHistory.object_id),
        LeftJoin(Sale, SaleItem.sale_id == Sale.id),
        LeftJoin(StockDecreaseItem,
                 StockDecreaseItem.id == StockTransactionHistory.object_id),
        LeftJoin(StockDecrease,
                 StockDecreaseItem.stock_decrease_id == StockDecrease.id),
    ]

    @property
    def total(self):
        return currency(abs(self.stock_cost * self.quantity))
