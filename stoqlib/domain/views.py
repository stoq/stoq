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

# pylint: enable=E1101

from kiwi.currency import currency
from storm.expr import (And, Coalesce, Eq, Join, LeftJoin, Or, Sum, Select,
                        Alias, Count, Cast, Ne)
from storm.info import ClassAlias

from stoqlib.database.expr import (Case, Distinct, Field, NullIf,
                                   StatementTimestamp, Concat)
from stoqlib.database.viewable import Viewable
from stoqlib.domain.account import Account, AccountTransaction
from stoqlib.domain.address import Address
from stoqlib.domain.commission import CommissionSource
from stoqlib.domain.costcenter import CostCenterEntry
from stoqlib.domain.fiscal import CfopData
from stoqlib.domain.loan import Loan, LoanItem
from stoqlib.domain.person import (Person, Supplier, Company, LoginUser,
                                   Branch, Client, Employee, Transporter,
                                   Individual, SalesPerson, ClientView)
from stoqlib.domain.product import (Product,
                                    ProductStockItem,
                                    ProductHistory,
                                    ProductManufacturer,
                                    ProductSupplierInfo,
                                    StockTransactionHistory,
                                    Storable, StorableBatch)
from stoqlib.domain.production import ProductionOrder, ProductionItem
from stoqlib.domain.purchase import (Quotation, QuoteGroup, PurchaseOrder,
                                     PurchaseItem)
from stoqlib.domain.receiving import (ReceivingOrderItem, ReceivingOrder,
                                      PurchaseReceivingMap)
from stoqlib.domain.sale import SaleItem, Sale, Delivery
from stoqlib.domain.returnedsale import ReturnedSale, ReturnedSaleItem
from stoqlib.domain.sellable import (Sellable, SellableUnit,
                                     SellableCategory,
                                     SellableTaxConstant)
from stoqlib.domain.stockdecrease import (StockDecrease, StockDecreaseItem)
from stoqlib.domain.workorder import WorkOrder, WorkOrderItem
from stoqlib.lib.decorators import cached_property


# Use a subselect to count the number of items, because that takes a lot less
# time (since it doesn't have a huge GROUP BY clause).
# Note that there are two subselects possible. The first should be used when the
# viewable is queried without the branch and the second when it is queried with
# the branch.
_StockSummary = Alias(Select(
    columns=[ProductStockItem.storable_id,
             Alias(None, 'branch_id'),
             Alias(Sum(ProductStockItem.quantity), 'stock'),
             Alias(Sum(ProductStockItem.quantity *
                       ProductStockItem.stock_cost), 'total_stock_cost')],
    tables=[ProductStockItem],
    group_by=[ProductStockItem.storable_id]), '_stock_summary')

# This subselect will be used to filter by branch, so it should include all
# possible (branch, storable) combinations so that all storables appear in the
# results
_StockBranchSummary = Alias(Select(
    columns=[Alias(Storable.id, 'storable_id'),
             Alias(Branch.id, 'branch_id'),
             Alias(Sum(ProductStockItem.quantity), 'stock'),
             Alias(Sum(ProductStockItem.quantity *
                       ProductStockItem.stock_cost), 'total_stock_cost')],
    tables=[Storable,
            # This is equivalent to a cross join
            Join(Branch, And(True)),
            LeftJoin(ProductStockItem, And(ProductStockItem.branch_id == Branch.id,
                                           ProductStockItem.storable_id == Storable.id))],
    group_by=[Storable.id, Branch.id]), '_stock_summary')

_price_search = Case(condition=And(StatementTimestamp() >= Sellable.on_sale_start_date,
                                   StatementTimestamp() <= Sellable.on_sale_end_date),
                     result=Sellable.on_sale_price,
                     else_=Sellable.base_price)


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
    price = _price_search
    has_image = Ne(Sellable.image_id, None)

    # Product
    product_id = Product.id
    parent_id = Product.parent_id
    location = Product.location
    model = Product.model
    brand = Product.brand
    ncm = Product.ncm

    manufacturer = ProductManufacturer.name
    tax_description = SellableTaxConstant.description
    category_description = SellableCategory.description
    unit = SellableUnit.description

    # Aggregates
    total_stock_cost = Coalesce(Field('_stock_summary', 'total_stock_cost'), 0)
    stock = Coalesce(Field('_stock_summary', 'stock'), 0)
    branch_id = Field('_stock_summary', 'branch_id')

    tables = [
        # Keep this first 4 joins in this order, so find_by_branch may change it.
        Sellable,
        Join(Product, Product.id == Sellable.id),
        LeftJoin(Storable, Storable.id == Product.id),
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

    def __eq__(self, other):
        # Viewable's __eq__ would only consider equal objects of the same
        # class, but the HighjackedViewable is an exception to the rule!
        if (other.__class__ in [
                self.__class__, getattr(self, '_highjacked_viewable', None)] or
            self.__class__ in [
                other.__class__, getattr(other, '_highjacked_viewable', None)]):
            return self.id == other.id

        return super(ProductFullStockView, self).__eq__(other)

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
        # Make sure to create it only once or else Viewable would fail to
        # compare both objects as their class would be different.
        if '_highjacked_viewable' not in cls.__dict__:
            tables = cls.tables[:]
            tables[3] = LeftJoin(_StockBranchSummary,
                                 Field('_stock_summary',
                                       'storable_id') == Storable.id)
            cls._highjacked_viewable = type(
                "Highjacked%s" % (cls.__name__, ),
                (cls, ),
                dict(tables=tables))

            # Make sure we will not create a highjack highjacked view
            cls._highjacked_viewable._highjacked_viewable = (
                cls._highjacked_viewable)

        # Also show products that were never purchased.
        query = Or(Field('_stock_summary', 'branch_id') == branch.id,
                   Eq(Field('_stock_summary', 'branch_id'), None))

        return store.find(cls._highjacked_viewable, query)

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

    def get_parent(self):
        if not self.parent_id:
            return None

        branch = self.branch_id and self.store.get(Branch, self.branch_id)
        res = self.find_by_branch(self.store, branch)
        return res.find(Product.id == self.parent_id).one()

    @property
    def stock_cost(self):
        if self.stock:
            return self.total_stock_cost / self.stock

        return 0

    @property
    def unit_description(self):
        unit = self.product.sellable.unit_description
        if unit == u"":
            return u"un"
        return unit


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

    clause = And(ProductFullStockView.clause, Eq(Product.is_composed, True))


class ProductComponentWithClosedView(ProductComponentView):
    """Stores information about production products, including closed ones"""

    clause = Eq(Product.is_composed, True)


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
        ProductFullStockView.stock > 0,
    )


class ProductWithStockBranchView(ProductFullStockView):
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

    tables = ProductFullStockView.tables[:]
    tables[3] = LeftJoin(_StockBranchSummary, storable_id == Storable.id)

    clause = And(ProductFullStockView.clause,
                 Eq(Product.is_grid, False),
                 Eq(Product.is_package, False))


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

    clause = And(ProductFullStockView.clause,
                 Eq(Product.is_grid, False))


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

    sellable = Sellable
    product = Product

    # Sellable
    id = Sellable.id
    code = Sellable.code
    description = Sellable.description

    # Product
    product_id = Product.id

    # ProductHistory
    branch = ProductHistory.branch_id
    sold_date = ProductHistory.sold_date
    received_date = ProductHistory.received_date
    production_date = ProductHistory.production_date
    decreased_date = ProductHistory.decreased_date

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
        Join(Product, Product.id == Sellable.id),
    ]

    # This are columns that are not supposed to be queried, but should still be
    # able to be filtered
    hidden_columns = ['sold_date', 'received_date', 'production_date',
                      'decreased_date']

    group_by = [id, product_id, code, description, branch]


class ProductBranchStockView(Viewable):
    """Stores information about the stock of a certain |product| among
    all branches
    """
    branch = Branch

    id = Branch.id
    branch_name = Coalesce(NullIf(Company.fancy_name, u''), Person.name)
    storable_id = ProductStockItem.storable_id
    stock = Sum(ProductStockItem.quantity)

    tables = [
        Branch,
        Join(Person, Person.id == Branch.person_id),
        Join(Company, Company.person_id == Person.id),
        Join(ProductStockItem, ProductStockItem.branch_id == Branch.id),
    ]

    group_by = [Branch, branch_name, storable_id]

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
    price = _price_search

    product_id = Product.id
    model = Product.model

    unit = SellableUnit.description
    manufacturer = ProductManufacturer.name
    category_description = SellableCategory.description

    stock = Coalesce(Field('_stock_summary', 'stock'), 0)
    # If the sellable is a service Product.internal_use will return None, so we
    # must add it to the query to include services
    clause = And(Or(Eq(Product.internal_use, False), Eq(Product.internal_use, None)),
                 Or(Eq(Product.is_grid, False), Eq(Product.is_grid, None)))

    tables = [
        Sellable,
        LeftJoin(SellableUnit, SellableUnit.id == Sellable.unit_id),
        LeftJoin(SellableCategory, SellableCategory.id == Sellable.category_id),
        LeftJoin(Product, Product.id == Sellable.id),
        LeftJoin(Storable, Storable.id == Product.id),
        LeftJoin(_StockBranchSummary,
                 Field('_stock_summary', 'storable_id') == Storable.id),
        LeftJoin(ProductManufacturer,
                 Product.manufacturer_id == ProductManufacturer.id),
    ]

    @classmethod
    def find_by_branch(cls, store, branch):
        assert branch
        query = Or(Field('_stock_summary', 'branch_id') == branch.id,
                   Eq(Field('_stock_summary', 'branch_id'), None))
        return store.find(cls, query)


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

    sellable = Sellable
    product = Product

    id = Sellable.id
    code = Sellable.code
    description = Sellable.description
    category = SellableCategory.description

    product_id = Product.id

    # Aggregate
    quantity = Sum(SaleItem.quantity)
    total_sold = Sum(SaleItem.price * SaleItem.quantity)
    total_cost = Sum(SaleItem.quantity * SaleItem.average_cost)

    tables = [
        Sellable,
        LeftJoin(Product, Product.id == Sellable.id),
        LeftJoin(SaleItem, Sellable.id == SaleItem.sellable_id),
        LeftJoin(Sale, SaleItem.sale_id == Sale.id),
        LeftJoin(SellableCategory, Sellable.category_id == SellableCategory.id),
    ]

    clause = Or(Sale.status == Sale.STATUS_CONFIRMED,
                Sale.status == Sale.STATUS_RENEGOTIATED)

    group_by = [id, product_id, code, description, category, Sale.status]

    @property
    def average_cost(self):
        if not self.quantity:  # pragma: nocoverage
            # FIXME: Will this ever happen?
            return 0
        return self.total_cost / self.quantity


class StockDecreaseView(Viewable):
    """Stores information about all stock decreases
    """
    _PersonBranch = ClassAlias(Person, "person_branch")
    _PersonSentTo = ClassAlias(Person, "person_sent_to")

    stock_decrease = StockDecrease

    id = StockDecrease.id
    identifier = StockDecrease.identifier
    confirm_date = StockDecrease.confirm_date
    reason = StockDecrease.reason
    cfop_description = CfopData.description
    branch_name = Coalesce(NullIf(Company.fancy_name, u''), _PersonBranch.name)
    removed_by_name = Person.name
    sent_to_name = _PersonSentTo.name

    # Aggregate
    total_items_removed = Sum(StockDecreaseItem.quantity)

    tables = [
        StockDecrease,
        Join(Employee, StockDecrease.removed_by_id == Employee.id),
        Join(Person, Employee.person_id == Person.id),
        Join(Branch, StockDecrease.branch_id == Branch.id),
        Join(_PersonBranch, Branch.person_id == _PersonBranch.id),
        LeftJoin(_PersonSentTo, StockDecrease.person_id == _PersonSentTo.id),
        Join(Company, Company.person_id == _PersonBranch.id),
        LeftJoin(CfopData, CfopData.id == StockDecrease.cfop_id),
        Join(StockDecreaseItem,
             StockDecreaseItem.stock_decrease_id == StockDecrease.id)
    ]

    group_by = [id, CfopData.id, Company.id, Person.id, _PersonBranch,
                _PersonSentTo]


class StockDecreaseItemsView(Viewable):
    """Stores information about all stock decrease items
    """
    branch = Branch

    id = StockDecreaseItem.id
    quantity = StockDecreaseItem.quantity
    sellable = StockDecreaseItem.sellable_id
    decrease_id = StockDecrease.id
    decrease_identifier = StockDecrease.identifier
    date = StockDecrease.confirm_date
    removed_by_name = Person.name
    unit_description = SellableUnit.description
    batch_number = Coalesce(StorableBatch.batch_number, u'')
    batch_date = StorableBatch.create_date

    tables = [
        StockDecreaseItem,
        LeftJoin(StorableBatch, StorableBatch.id == StockDecreaseItem.batch_id),
        Join(StockDecrease, StockDecreaseItem.stock_decrease_id == StockDecrease.id),
        LeftJoin(Sellable, StockDecreaseItem.sellable_id == Sellable.id),
        LeftJoin(SellableUnit, Sellable.unit_id == SellableUnit.id),
        Join(Employee, StockDecrease.removed_by_id == Employee.id),
        Join(Person, Employee.person_id == Person.id),
        Join(Branch, StockDecrease.branch_id == Branch.id),
    ]


class SoldItemsByBranchView(SoldItemView):
    """Store information about the all sold items by branch.
    """

    branch_name = Coalesce(NullIf(Company.fancy_name, u''), Person.name)

    # Aggregates
    total = Sum(SaleItem.quantity * SaleItem.price)

    tables = SoldItemView.tables[:]
    tables.extend([
        LeftJoin(Branch, Branch.id == Sale.branch_id),
        LeftJoin(Person, Branch.person_id == Person.id),
        LeftJoin(Company, Company.person_id == Person.id),
    ])

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

    sellable = Sellable
    product = Product

    purchase_item = PurchaseItem
    branch = Branch

    id = PurchaseItem.id
    purchased = PurchaseItem.quantity
    received = PurchaseItem.quantity_received
    expected_receival_date = PurchaseItem.expected_receival_date

    order_identifier = PurchaseOrder.identifier
    order_identifier_str = Cast(PurchaseOrder.identifier, 'text')
    purchased_date = PurchaseOrder.open_date
    branch_id = PurchaseOrder.branch_id

    sellable_id = Sellable.id
    code = Sellable.code
    description = Sellable.description

    product_id = Product.id

    # Aggregate
    stocked = Sum(ProductStockItem.quantity)

    tables = [
        PurchaseItem,
        LeftJoin(PurchaseOrder, PurchaseItem.order_id == PurchaseOrder.id),
        LeftJoin(Branch, PurchaseOrder.branch_id == Branch.id),
        LeftJoin(Sellable, Sellable.id == PurchaseItem.sellable_id),
        LeftJoin(Product, Product.id == PurchaseItem.sellable_id),
        LeftJoin(Storable, Storable.id == Product.id),
        LeftJoin(ProductStockItem, ProductStockItem.storable_id == Storable.id),
    ]

    clause = And(PurchaseOrder.status == PurchaseOrder.ORDER_CONFIRMED,
                 PurchaseOrder.branch_id == ProductStockItem.branch_id,
                 PurchaseItem.quantity > PurchaseItem.quantity_received, )

    group_by = [PurchaseItem, Branch, order_identifier, purchased_date,
                branch_id, code, description, sellable_id, product_id]


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
        LeftJoin(PurchaseReceivingMap,
                 ReceivingOrder.id == PurchaseReceivingMap.receiving_id),
        LeftJoin(PurchaseOrder, PurchaseReceivingMap.purchase_id == PurchaseOrder.id),
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

    branch = Branch
    sellable = Sellable
    product = Product

    id = SaleItem.id
    sellable_id = Sellable.id
    code = Sellable.code
    description = Sellable.description
    category = SellableCategory.description
    sale_id = SaleItem.sale_id
    sale_identifier = Sale.identifier
    sale_date = Sale.open_date
    client_id = Client.id
    client_name = Person.name
    quantity = SaleItem.quantity
    price = SaleItem.price
    base_price = SaleItem.base_price
    parent_item_id = SaleItem.parent_item_id
    manufacturer = ProductManufacturer.name
    unit_description = SellableUnit.description
    batch_number = Coalesce(StorableBatch.batch_number, u'')
    batch_date = StorableBatch.create_date

    item_discount = SaleItem.base_price - SaleItem.price
    total = SaleItem.price * SaleItem.quantity

    tables = [
        SaleItem,
        LeftJoin(StorableBatch, StorableBatch.id == SaleItem.batch_id),
        LeftJoin(Sellable, Sellable.id == SaleItem.sellable_id),
        LeftJoin(SellableCategory, SellableCategory.id == Sellable.category_id),
        LeftJoin(Product, Product.id == Sellable.id),
        LeftJoin(ProductManufacturer,
                 ProductManufacturer.id == Product.manufacturer_id),
        Join(Sale, SaleItem.sale_id == Sale.id),
        LeftJoin(SellableUnit, Sellable.unit_id == SellableUnit.id),
        LeftJoin(Client, Sale.client_id == Client.id),
        LeftJoin(Person, Client.person_id == Person.id),
        Join(Branch, Sale.branch_id == Branch.id),
    ]

    #
    # Class methods
    #

    @classmethod
    def find_confirmed(cls, store, sellable):
        clause = And(Sellable.id == sellable.id,
                     Or(Sale.status == Sale.STATUS_CONFIRMED,
                        Sale.status == Sale.STATUS_RENEGOTIATED,
                        Sale.status == Sale.STATUS_ORDERED))
        return store.find(cls, clause)

    @classmethod
    def find_parent_items(cls, store, sale):
        clause = And(cls.sale_id == sale.id,
                     Eq(cls.parent_item_id, None))
        return store.find(cls, clause)

    #
    # Public API
    #

    def get_children(self):
        return self.store.find(SaleItemsView, SaleItemsView.parent_item_id == self.id)


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

    branch = Branch

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
    batch_number = Coalesce(StorableBatch.batch_number, u'')
    batch_date = StorableBatch.create_date

    tables = [
        ReceivingOrderItem,
        LeftJoin(StorableBatch, StorableBatch.id == ReceivingOrderItem.batch_id),
        Join(ReceivingOrder,
             ReceivingOrderItem.receiving_order_id == ReceivingOrder.id),
        Join(PurchaseReceivingMap,
             ReceivingOrder.id == PurchaseReceivingMap.receiving_id),
        Join(PurchaseOrder, PurchaseReceivingMap.purchase_id == PurchaseOrder.id),
        LeftJoin(Sellable, ReceivingOrderItem.sellable_id == Sellable.id),
        LeftJoin(SellableUnit, Sellable.unit_id == SellableUnit.id),
        LeftJoin(Supplier, ReceivingOrder.supplier_id == Supplier.id),
        LeftJoin(Person, Supplier.person_id == Person.id),
        Join(Branch, PurchaseOrder.branch_id == Branch.id),
    ]


class ProductionItemView(Viewable):
    production_item = ProductionItem
    sellable = Sellable
    product = Product

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
                 Sellable.id == Product.id),
        LeftJoin(SellableCategory,
                 SellableCategory.id == Sellable.category_id),
        LeftJoin(SellableUnit,
                 Sellable.unit_id == SellableUnit.id),
    ]


class ProductBatchView(Viewable):

    sellable = Sellable
    product = Product

    id = ProductStockItem.id
    branch_name = Company.fancy_name
    description = Sellable.description
    quantity = ProductStockItem.quantity
    batch_number = Coalesce(StorableBatch.batch_number, u'')
    batch_date = StorableBatch.create_date
    category = SellableCategory.description
    manufacturer = ProductManufacturer.name
    model = Product.model
    brand = Product.brand

    tables = [
        ProductStockItem,
        Join(Branch, ProductStockItem.branch_id == Branch.id),
        Join(Company, Branch.person_id == Company.person_id),
        LeftJoin(StorableBatch, ProductStockItem.batch_id == StorableBatch.id),
        Join(Storable, ProductStockItem.storable_id == Storable.id),
        Join(Product, Storable.id == Product.id),
        Join(Sellable, Product.id == Sellable.id),
        LeftJoin(ProductManufacturer,
                 Product.manufacturer_id == ProductManufacturer.id),
        LeftJoin(SellableCategory, Sellable.category_id == SellableCategory.id)
    ]

    clause = ProductStockItem.quantity > 0


class ProductBrandByBranchView(Viewable):
    branch = Branch

    # The tuple (brand, branch, manufacturer, category) is unique, so we can use as id
    id = Concat(Product.brand,
                Cast(Branch.id, "text"),
                Coalesce(ProductManufacturer.name, u''),
                Coalesce(SellableCategory.description, u''))
    brand = Coalesce(Product.brand, u'')
    manufacturer = ProductManufacturer.name
    product_category = SellableCategory.description

    branch_id = Branch.id

    company = Company.fancy_name

    quantity = Sum(ProductStockItem.quantity)

    tables = [
        ProductStockItem,
        Join(Storable, Storable.id == ProductStockItem.storable_id),
        Join(Product, Product.id == Storable.id),
        LeftJoin(ProductManufacturer,
                 ProductManufacturer.id == Product.manufacturer_id),
        Join(Branch, Branch.id == ProductStockItem.branch_id),
        Join(Person, Person.id == Branch.person_id),
        Join(Company, Company.person_id == Person.id),
        Join(Sellable, Product.id == Sellable.id),
        LeftJoin(SellableCategory, Sellable.category_id == SellableCategory.id),
    ]

    clause = ProductStockItem.quantity > 0

    group_by = [id, brand, Branch.id, Company.id, ProductManufacturer.id,
                SellableCategory.id]

    @classmethod
    def find_by_category(cls, store, category):
        queries = []
        if category:
            queries.append(Sellable.category == category)
        if queries:
            return store.find(cls, And(*queries))

        return store.find(cls)

    @classmethod
    def find_by_branch(cls, store, branch):
        return store.find(cls, branch_id=branch.id)


class ProductBrandStockView(Viewable):
    # Alias of Branch to Person table

    id = Product.brand
    brand = Coalesce(Product.brand, u'')

    quantity = Sum(ProductStockItem.quantity)
    company = u''

    tables = [
        Product,
        LeftJoin(Storable,
                 Storable.id == Product.id),
        LeftJoin(ProductStockItem,
                 ProductStockItem.storable_id == Storable.id),
        LeftJoin(Sellable, Sellable.id == Product.id),
        LeftJoin(Branch, Branch.id == ProductStockItem.branch_id)
    ]
    group_by = [id, brand]


class UnconfirmedSaleItemsView(Viewable):
    """Stores information about reserved products
    This view is used to query products that was reserved
    and temporarily removed from stock until the sale is completed.

    :cvar id: the id of the reserved sale item
    :cvar price: the price when it was reserved
    :cvar quantity_decreased: quantity reserved
    :cvar open_date: when the sale was open
    :cvar status: status of a sale can be STATUS_ORDERED or STATUS_QUOTE
    :cvar description: the description of a product
    :cvar client_name: stores who reserved the product
    :cvar salesperson_name: stores the sales person
    """
    PersonClient = ClassAlias(Person, 'person_client')
    PersonSales = ClassAlias(Person, 'person_sales')

    branch = Branch

    id = SaleItem.id
    price = SaleItem.price
    quantity = SaleItem.quantity
    quantity_decreased = SaleItem.quantity_decreased
    total = SaleItem.price * SaleItem.quantity

    branch_id = Sale.branch_id
    sale_id = Sale.id
    identifier = Sale.identifier
    open_date = Sale.open_date
    status = Sale.status

    description = Sellable.description
    product_category = SellableCategory.description
    product_code = Sellable.code
    client_name = PersonClient.name
    salesperson_name = PersonSales.name
    manufacturer_name = ProductManufacturer.name

    wo_identifier = WorkOrder.identifier
    wo_identifier_str = Cast(WorkOrder.identifier, 'text')
    wo_status = WorkOrder.status
    wo_estimated_finish = WorkOrder.estimated_finish
    wo_finish = WorkOrder.finish_date

    tables = [
        SaleItem,
        Join(Sale, Sale.id == SaleItem.sale_id),
        Join(Sellable, Sellable.id == SaleItem.sellable_id),
        Join(Branch, Branch.id == Sale.branch_id),
        Join(SalesPerson, SalesPerson.id == Sale.salesperson_id),
        Join(PersonSales, PersonSales.id == SalesPerson.person_id),
        LeftJoin(Product, Product.id == Sellable.id),
        LeftJoin(ProductManufacturer, ProductManufacturer.id == Product.manufacturer_id),
        LeftJoin(Client, Client.id == Sale.client_id),
        LeftJoin(PersonClient, PersonClient.id == Client.person_id),
        LeftJoin(SellableCategory, Sellable.category_id == SellableCategory.id),
        LeftJoin(WorkOrderItem, WorkOrderItem.sale_item == SaleItem.id),
        LeftJoin(WorkOrder, WorkOrder.id == WorkOrderItem.order_id)
    ]

    clause = Or(Sale.status == Sale.STATUS_ORDERED,
                Sale.status == Sale.STATUS_QUOTE)

    @property
    def status_str(self):
        return Sale.statuses[self.status]

    @property
    def wo_status_str(self):
        if not self.wo_identifier:
            return ''
        return WorkOrder.statuses[self.wo_status]


class ReturnedSalesView(Viewable):
    PersonBranch = ClassAlias(Person, 'person_branch')
    PersonResponsible = ClassAlias(Person, 'responsible_sale')
    PersonClient = ClassAlias(Person, 'person_client')

    returned_sale = ReturnedSale

    #: The branch this sale was sold
    branch = Branch

    #: The sale that is being returned
    sale = Sale

    id = ReturnedSale.id
    identifier = ReturnedSale.identifier
    identifier_str = Cast(ReturnedSale.identifier, 'text')
    return_date = ReturnedSale.return_date
    reason = ReturnedSale.reason
    invoice_number = ReturnedSale.invoice_number
    receiving_date = ReturnedSale.confirm_date
    receiving_responsible = ReturnedSale.confirm_responsible_id
    status = ReturnedSale.status

    sale_id = Sale.id
    sale_identifier_str = Cast(Sale.identifier, 'text')

    responsible_name = PersonResponsible.name
    branch_name = Coalesce(NullIf(Company.fancy_name, u''), PersonBranch.name)
    client_name = PersonClient.name

    tables = [
        ReturnedSale,
        Join(Sale, Sale.id == ReturnedSale.sale_id),
        Join(LoginUser, LoginUser.id == ReturnedSale.responsible_id),
        Join(PersonResponsible, PersonResponsible.id == LoginUser.person_id),
        Join(Branch, Branch.id == ReturnedSale.branch_id),
        Join(PersonBranch, PersonBranch.id == Branch.person_id),
        Join(Company, Company.person_id == PersonBranch.id),
        LeftJoin(Client, Client.id == Sale.client_id),
        LeftJoin(PersonClient, PersonClient.id == Client.person_id),
    ]

    @property
    def sale_identifier(self):
        return self.sale.identifier

    def can_receive(self):
        from stoqlib.api import api
        same_branch = self.sale.branch == api.get_current_branch(self.store)
        return bool(self.is_pending() and same_branch)

    def is_pending(self):
        return self.returned_sale.is_pending()

    @property
    def status_str(self):
        return ReturnedSale.statuses[self.status]


class ReturnedItemView(ReturnedSalesView):
    sellable = Sellable
    product = Product

    id = ReturnedSaleItem.id
    item_description = Sellable.description
    item_quantity = ReturnedSaleItem.quantity

    tables = ReturnedSalesView.tables[:]

    tables.extend([Join(ReturnedSaleItem,
                        ReturnedSale.id == ReturnedSaleItem.returned_sale_id),
                   Join(Sellable, ReturnedSaleItem.sellable_id == Sellable.id),
                   LeftJoin(Product, Sellable.id == Product.id)])


class PendingReturnedSalesView(ReturnedSalesView):

    clause = ReturnedSale.status == ReturnedSale.STATUS_PENDING


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

    branch_name = Coalesce(NullIf(Company.fancy_name, u''), PersonBranch.name)
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
        LeftJoin(Company, Company.person_id == PersonBranch.id),
        LeftJoin(PersonResponsible,
                 LoginUser.person_id == PersonResponsible.id),
        LeftJoin(PersonClient, Client.person_id == PersonClient.id),
    ]

    group_by = [Loan, branch_name, responsible_name, client_name]


class LoanItemView(Viewable):
    sellable = Sellable
    product = Product
    branch = Branch

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

    product_id = Product.id
    batch_number = Coalesce(StorableBatch.batch_number, u'')
    batch_date = StorableBatch.create_date

    category_description = SellableCategory.description
    unit_description = SellableUnit.description

    identifier_str = Cast(Loan.identifier, 'text')

    tables = [
        LoanItem,
        LeftJoin(StorableBatch, StorableBatch.id == LoanItem.batch_id),
        Join(Loan, LoanItem.loan_id == Loan.id),
        Join(Branch, Loan.branch_id == Branch.id),
        LeftJoin(Sellable, LoanItem.sellable_id == Sellable.id),
        LeftJoin(Product, Product.id == Sellable.id),
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
        Join(Sellable, StockTransactionHistory.storable_id == Sellable.id),

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


class ClientWithSalesView(ClientView):
    """A client view capable of filtering clients with sales on a given branch."""

    tables = ClientView.tables[:]
    tables.extend([
        LeftJoin(Sale,
                 Sale.client_id == Client.id),
        LeftJoin(Branch,
                 Sale.branch_id == Branch.id),
    ])

    @classmethod
    def find_by_birth_date(cls, store, date, branch=None):
        """Find clients by bith date.

        :param store: The store used to do the query
        :param date: The date to filter the birthdays, either the
            value directly or a tuple defining a (start, end) interval
        :param branch: If not ``None`` will be used to filter only clients
            with at least one sale referencing it done on that |branch|
        """
        assert date is not None

        # If we are finding by birth date, exclude those without that
        # information by default
        query = [Ne(cls.birth_date, None)]

        if branch is not None:
            query.append(Branch.id == branch.id)

        if isinstance(date, tuple):
            query.append(Individual.get_birthday_query(
                date[0], date[1]))
        else:
            query.append(Individual.get_birthday_query(date))

        res = store.find(cls, And(*query))
        res.config(distinct=True)
        return res
