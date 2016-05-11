# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2013 Async Open Source <http://www.async.com.br>
## All rights reserved
##
## This program is free software; you can redistribute it and/or modify
## it under the terms of the GNU Lesser General Public License as published by
## the Free Software Foundation; either version 2 of the License, or
## (at your option) any later version.
##
## This program is distributed in the hope that it will be useful,
## but WITHOUT ANY WARRANTY; without even the implied warranty of
## MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
## GNU Lesser General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>

"""
Product, a physical goods that can be purchased, stored and sold.
It's purchased by a supplier and sold to client.

Imports that will be used in this doctest:

    >>> from stoqlib.database.runtime import new_store, get_current_branch
    >>> from stoqlib.domain.product import Product, ProductStockItem, Storable
    >>> from stoqlib.domain.product import StockTransactionHistory

Create a new store

    >>> store = new_store()

Create a branch we can use:

    >>> from stoqlib.domain.exampledata import ExampleCreator
    >>> branch = ExampleCreator.create(store, 'Branch')

Create a sellable we can use:

    >>> from stoqlib.domain.exampledata import ExampleCreator
    >>> sellable = ExampleCreator.create(store, 'Sellable')

The ExampleCreator already creates a Product for us. Now lets attach it a
storable facet.

    >>> product = sellable.product
    >>> storable = Storable(product=product, store=store)

The storable needs to have it's stock created, let's do so. Note that a reason
is always required when changing the stock quantity

    >>> storable.increase_stock(10, branch, StockTransactionHistory.TYPE_INITIAL, None)

A stock item should now be available for the storable:

    >>> stock_item = storable.get_stock_item(branch, batch=None)

The branch and storable should be set properly

    >>> stock_item.branch == branch
    True

    >>> stock_item.storable == storable
    True

Fetch the stock item for the current branch and verify that the
stock_items are unique:

    >>> current_branch = get_current_branch(store)
    >>> stock_item2 = storable.get_stock_item(current_branch, batch=None)
    >>> stock_item != stock_item2
    True

    >>> store.close()

"""

# pylint: enable=E1101

from decimal import Decimal

from kiwi.currency import currency
from storm.references import Reference, ReferenceSet
from storm.expr import (And, Eq, LeftJoin, Alias, Sum, Coalesce, Select, Join, Cast)
from zope.interface import implementer

from stoqlib.database.expr import (Field, TransactionTimestamp,
                                   ArrayAgg, Contains, IsContainedBy,
                                   SplitPart)
from stoqlib.database.properties import (BoolCol, DateTimeCol, DecimalCol,
                                         EnumCol, IdCol, IntCol, PercentCol,
                                         PriceCol, QuantityCol, UnicodeCol)
from stoqlib.database.runtime import get_current_user, autoreload_object
from stoqlib.database.viewable import Viewable
from stoqlib.domain.base import Domain
from stoqlib.domain.events import (ProductCreateEvent, ProductEditEvent,
                                   ProductRemoveEvent, ProductStockUpdateEvent)
from stoqlib.domain.interfaces import IDescribable
from stoqlib.domain.person import Person, Branch
from stoqlib.domain.sellable import Sellable
from stoqlib.exceptions import StockError
from stoqlib.lib.dateutils import localnow, localtoday
from stoqlib.lib.stringutils import next_value_for
from stoqlib.lib.translation import stoqlib_gettext, stoqlib_ngettext

_ = stoqlib_gettext

#
# pyflakes
#
Person  # pylint: disable=W0104


class ProductSupplierInfo(Domain):
    """Supplier information for a |product|.

    Each product can has more than one |supplier|.

    See also:
    `schema <http://doc.stoq.com.br/schema/tables/product_supplier_info.html>`__
    """

    __storm_table__ = 'product_supplier_info'

    #: the cost which helps the purchaser to define the main cost of a
    #: certain product. Each product can have multiple |suppliers| and for
    #: each |supplier| a base_cost is available. The purchaser in this case
    #: must decide how to define the main cost based in the base cost avarage
    #: of all suppliers.
    base_cost = PriceCol(default=0)

    notes = UnicodeCol(default=u'')

    #: if this object stores information for the main |supplier|.
    is_main_supplier = BoolCol(default=False)

    #: the number of days needed to deliver the product to purchaser.
    lead_time = IntCol(default=1)

    #: the minimum amount that we can buy from this supplier.
    minimum_purchase = QuantityCol(default=Decimal(1))

    #: a Brazil-specific attribute that means 'Imposto sobre circulacao
    #: de mercadorias e prestacao de servicos'
    icms = PercentCol(default=0)

    supplier_id = IdCol()

    #: the |supplier|
    supplier = Reference(supplier_id, 'Supplier.id')

    product_id = IdCol()

    #: the |product|
    product = Reference(product_id, 'Product.id')

    #: the product code in the supplier
    supplier_code = UnicodeCol(default=u'')

    #
    # Auxiliary methods
    #

    def get_name(self):
        if self.supplier:
            return self.supplier.get_description()

    def get_lead_time_str(self):
        return u"%d %s" % (
            self.lead_time,
            stoqlib_ngettext(_(u"Day"), _(u"Days"), self.lead_time))


class Product(Domain):
    """A Product is a thing that can be:

      * ordered (via |purchase|)
      * stored (via |storable|)
      * sold (via |sellable|)
      * manufactured (via |production|)

    A manufactured product can have several |components|, which are parts
    that when combined create the product.

    A consigned product is borrowed from a |supplier|. You can also loan out
    your own products via |loan|.

    If the product does not use stock managment, it will be possible to sell
    items, even if it was never purchased.

    See also:
    `schema <http://doc.stoq.com.br/schema/tables/product.html>`__
    """

    __storm_table__ = 'product'

    TYPE_COMMON = 0
    TYPE_BATCH = 1
    TYPE_WITHOUT_STOCK = 2
    TYPE_CONSIGNED = 3
    TYPE_GRID = 4
    TYPE_PACKAGE = 5

    product_types = {
        TYPE_COMMON: _("Regular product"),
        TYPE_BATCH: _("Product with batch control"),
        TYPE_WITHOUT_STOCK: _("Product without stock control"),
        TYPE_CONSIGNED: _("Consigned product"),
        TYPE_GRID: _("Grid product"),
        TYPE_PACKAGE: _("Package product"),
    }

    #: |sellable| for this product
    sellable = Reference('id', 'Sellable.id')

    #: if this product is loaned from the |supplier|
    consignment = BoolCol(default=False)

    #: ``True`` if this product has |components|.
    #: This is stored on Product to avoid a join to find out if there is any
    #: components or not.
    is_composed = BoolCol(default=False)

    #: ``True`` if this product is parent of another product.
    #: This is also an indication that this product will have other products
    #: "attached" to itself
    is_grid = BoolCol(default=False)

    #: id of his parent
    parent_id = IdCol()
    #: Indicates the parent of this product.
    parent = Reference(parent_id, 'Product.id')

    #: If this product will use stock management.
    #: When this is set to ``True``, a corresponding |storable| should be created.
    #: For ``False`` a storable will not be created and the quantity currently
    #: in stock will not be known, e.g. |purchases| will not increase the stock
    # quantity, and the operations that decrease stock (like a |sale| or a
    # |loan|, will be allowed at any time.
    manage_stock = BoolCol(default=True)

    #: physical location of this product, like a drawer or shelf number
    location = UnicodeCol(default=u'')

    manufacturer_id = IdCol(default=None)

    #: name of the manufacturer for this product, eg "General Motors"
    manufacturer = Reference(manufacturer_id, 'ProductManufacturer.id')

    #: name of the brand, eg "Chevrolet" or "Opel"
    brand = UnicodeCol(default=u'')

    #: name of the family, eg "Cobalt" or "Astra"
    family = UnicodeCol(default=u'')

    #: name of the model, eg "2.2 L Ecotec L61 I4" or "2.0 8V/ CD 2.0 Hatchback 5p Aut"
    model = UnicodeCol(default=u'')

    #: a number representing this part
    part_number = UnicodeCol(default=u'')

    #: physical width of this product, unit not enforced
    width = DecimalCol(default=0)

    #: physical height of this product, unit not enforced
    height = DecimalCol(default=0)

    #: depth in this product, unit not enforced
    depth = DecimalCol(default=0)

    #: physical weight of this product, unit not enforced
    weight = DecimalCol(default=0)

    #: The time in days it takes to manufacter this product
    production_time = IntCol(default=1)

    #: Brazil specific: NFE: nomenclature comon do mercuosol
    ncm = UnicodeCol(default=None)

    #: NFE: see ncm
    ex_tipi = UnicodeCol(default=None)

    #: NFE: see ncm
    genero = UnicodeCol(default=None)

    #: Id of ICMS tax in product tax template
    icms_template_id = IdCol(default=None)

    #: the :class:`stoqlib.domain.taxes.ProductIcmsTemplate` tax for *self*
    icms_template = Reference(icms_template_id, 'ProductIcmsTemplate.id')

    #: Id of IPI tax in product tax template
    ipi_template_id = IdCol(default=None)

    #: the :class:`stoqlib.domain.taxes.ProductIpiTemplate` tax for *self*
    ipi_template = Reference(ipi_template_id, 'ProductIpiTemplate.id')

    #: Id of PIS tax in product tax template
    pis_template_id = IdCol(default=None)

    #: the :class:`stoqlib.domain.taxes.ProductPisTemplate` tax for *self*
    pis_template = Reference(pis_template_id, 'ProductPisTemplate.id')

    #: Id of COFINS tax in product tax template
    cofins_template_id = IdCol(default=None)

    #: the :class:`stoqlib.domain.taxes.ProductCofinsTemplate` tax for *self*
    cofins_template = Reference(cofins_template_id, 'ProductCofinsTemplate.id')

    #: Used for composed products only
    quality_tests = ReferenceSet('id', 'ProductQualityTest.product_id')

    #: list of |suppliers| that sells this product
    suppliers = ReferenceSet('id', 'ProductSupplierInfo.product_id')

    #: list of |product| that is child of this product
    children = ReferenceSet('id', 'Product.parent_id')

    #: list of |product_attribute| of this product
    attributes = ReferenceSet('id', 'ProductAttribute.product_id')

    #: list of |grid_option| of this product
    grid_options = ReferenceSet('id', 'ProductOptionMap.product_id')

    #: the |storable| for this product
    storable = Reference('id', 'Storable.id', on_remote=True)

    #: This indicaters if this product is only used internally by the store.
    #: This means this product can be bought but cannot be sold
    internal_use = BoolCol(default=False)

    # Indicates if the product is a of TYPE_PACKAGE
    is_package = BoolCol(default=False)

    def __init__(self, **kwargs):
        assert 'sellable' in kwargs
        kwargs['id'] = kwargs['sellable'].id

        super(Product, self).__init__(**kwargs)

    #
    # Properties
    #

    @property
    def description(self):
        return self.sellable.description

    @property
    def product_type(self):
        storable = self.storable

        if self.is_grid:
            return self.TYPE_GRID
        elif not self.manage_stock and not self.is_package:
            assert storable is None
            return self.TYPE_WITHOUT_STOCK
        elif self.is_package:
            assert storable is None
            return self.TYPE_PACKAGE
        elif storable.is_batch:
            return self.TYPE_BATCH
        elif self.consignment:
            return self.TYPE_CONSIGNED
        else:
            return self.TYPE_COMMON

    @property
    def product_type_str(self):
        return self.product_types[self.product_type]

    #
    # Private
    #

    def _copy_product_suppliers(self, target):
        """Copy the suppliers reference set from self to a target product

        :param target: The target |product| for the suppliers copy.
        :returns: A |ProductSupplierInfo| ReferenceSet
        """
        # This dictionary is used as reference to tell us if the target has a
        # supplier that it's parent doesn't.
        target_suppliers = {info.supplier: info for info in target.suppliers}

        props = ['base_cost', 'notes', 'is_main_supplier', 'lead_time',
                 'minimum_purchase', 'icms', 'supplier']
        for info in self.suppliers:
            try:
                # If this supplier is already related to the target, we will
                # update it. We also pop it from our reference dictionary.
                prod_sup = target_suppliers.pop(info.supplier)
            except KeyError:
                # If the supplier isn't in the dictionary, that means we must
                # create it for the target.
                prod_sup = ProductSupplierInfo(product=target)

            for prop in props:
                value = getattr(info, prop)
                setattr(prod_sup, prop, value)

        # If there is something left in the target_suppliers, this means those
        # suppliers are not related to the parent anymore. So we remove it.
        for info in target_suppliers.values():
            target.store.remove(info)

        return target

    #
    #  Public API
    #

    def set_as_storable_product(self, quantity=0):
        """ Change a product without storable to a product with stock control.

        :param quantity: The current product quantity in stock.
        """
        assert self.product_type == self.TYPE_WITHOUT_STOCK
        # FIXME: On first time, only creating a common product.
        # After, also choose between create a consigned or a product with batch control
        from stoqlib.database.runtime import get_current_branch
        branch = get_current_branch(store=self.store)
        storable = Storable(product=self, store=self.store)

        # TODO: Instead of register an initial stock, we must consider the product history.
        # Calculating the current quantity based on stock transaction history.
        storable.register_initial_stock(quantity, branch, self.sellable.cost)
        self.manage_stock = True

    def has_quality_tests(self):
        return not self.quality_tests.find().is_empty()

    def remove(self):
        """Deletes this product from the database.
        """
        for child in self.children:
            child.sellable.remove()
        for attr in self.attributes:
            self.store.remove(attr)
        storable = self.storable
        if storable:
            self.store.remove(storable)
        for option in self.grid_options:
            self.store.remove(option)
        for supplier in self.get_suppliers_info():
            self.store.remove(supplier)
        for component in self.get_components():
            self.store.remove(component)
        self.store.remove(self)

    def can_remove_children(self):
        """Checks if this product's children can be removed
        """
        return all(child.sellable.can_remove() for child in self.children)

    def can_remove(self):
        """Whether we can delete this product and it's |sellable| from the
        database.

        ``False`` if the product was sold, received or used in a
        production. ``True`` otherwise.
        """
        if self.is_grid:
            return self.can_remove_children()

        if self.storable and not self.storable.can_remove():
            return False

        return super(Product, self).can_remove(
            skip=[('storable', 'id'),
                  ('product_supplier_info', 'product_id'),
                  ('product_option_map', 'product_id'),
                  ('product_component', 'product_id')])

    def can_close_children(self):
        """Checks if this product's children can be closed

        Called by |self| to check if it's children can be closed or not.
        A product child can be closed if it doesn't have any stock left
        """
        return all(child.sellable.can_close() for child in self.children)

    def can_close(self):
        """Checks if this product can be closed

        Called by |sellable| to check if it can be closed or not.
        A product can be closed if it doesn't have any stock left
        """
        if self.is_grid:
            return self.can_close_children()
        if self.manage_stock:
            return self.storable.get_total_balance() == 0
        return True

    def close(self):
        """Closes the product's children
        """
        for child in self.children:
            child.sellable.close()

    def get_manufacture_time(self, quantity, branch):
        """Returns the estimated time in days to manufacture a product

        If the |components| don't have enough stock, the estimated time to
        obtain missing |components| will also be considered (using the max
        lead time from the |suppliers|)

        :param quantity:
        :param branch: the |branch|
        """
        assert self.is_composed

        # Components maximum lead time
        comp_max_time = 0
        for i in self.get_components():
            # Products without manage stock control doesnt have storable
            if not i.component.manage_stock:
                continue
            storable = i.component.storable
            needed = quantity * i.quantity
            stock = storable.get_balance_for_branch(branch)
            # We have enough of this component items to produce.
            if stock >= needed:
                continue
            comp_max_time = max(comp_max_time,
                                i.component.get_max_lead_time(needed, branch))
        return self.production_time + comp_max_time

    def get_max_lead_time(self, quantity, branch):
        """Returns the longest lead time for this product.

        If this is a composed product, the lead time will be the time to
        manufacture the product plus the time to obtain all the missing
        components

        If its a regular product this will be the longest lead time for a
        supplier to deliver the product (considering the worst case).

        quantity and |branch| are used only when the product is composed
        """
        if self.is_composed:
            return self.get_manufacture_time(quantity, branch)
        else:
            return self.suppliers.find().max(ProductSupplierInfo.lead_time) or 0

    def get_main_supplier_name(self):
        supplier_info = self.get_main_supplier_info()
        if supplier_info is not None:
            return supplier_info.get_name()

    def get_main_supplier_info(self):
        """Gets a list of main suppliers for a Product, the main supplier
        is the most recently selected supplier.

        :returns: main supplier info
        :rtype: ProductSupplierInfo or None if a product lacks
           a main suppliers
        """
        store = self.store
        return store.find(ProductSupplierInfo,
                          product=self, is_main_supplier=True).one()

    def get_suppliers_info(self):
        """Returns a list of suppliers for this product

        :returns: a list of suppliers
        :rtype: list of ProductSupplierInfo
        """
        return self.store.find(ProductSupplierInfo,
                               product=self)

    def get_product_supplier_code(self, supplier):
        query = And(ProductSupplierInfo.product == self.id,
                    ProductSupplierInfo.supplier == supplier)
        return self.store.find(ProductSupplierInfo.supplier_code, query).one()

    def get_product_supplier_info(self, supplier):
        """Returns the product information for the specified supplier.

        :param supplier: the |supplier|
        :returns: The supplier's product information
        :rtype: :class:'ProductSupplierInfo'
        """
        query = And(ProductSupplierInfo.product == self,
                    ProductSupplierInfo.supplier == supplier)
        return self.store.find(ProductSupplierInfo, query).one()

    def get_components(self):
        """Returns the products which are our |components|.

        :returns: a sequence of |components|
        """
        return self.store.find(ProductComponent, product=self)

    def has_components(self):
        """Returns if this product has a |component| or not.

        :returns: ``True`` if this product has |components|, ``False`` otherwise.
        """
        return self.get_components().count() > 0

    def get_production_cost(self):
        """ Return the production cost of one unit of the product.

        :returns: the production cost
        """
        return self.sellable.cost

    def is_supplied_by(self, supplier):
        """If this product is supplied by the given |supplier|, returns the
        object with the supplier information. Returns ``None`` otherwise
        """
        store = self.store
        return store.find(ProductSupplierInfo, product=self,
                          supplier=supplier).one() is not None

    def is_composed_by(self, product):
        """Returns if we are composed by a given product or not.

        :param product: a possible component of this product
        :returns: ``True`` if the given product is one of our component or a
          component of our components, otherwise ``False``.
        """
        for component in self.get_components():
            if product is component.component:
                return True
            if component.component.is_composed_by(product):
                return True
        return False

    def child_exists(self, options):
        """Check if the child already exists

        :param options: a list of |grid_option| that the child should match
        :returns: True if the child exists, otherwise ``False``
        """

        tables = [ProductOptionMap,
                  Join(Product, Product.id == ProductOptionMap.product_id)]
        query = Product.parent == self
        data = self.store.using(*tables).find(ProductOptionMap.product_id, query)

        # Here we are combining all the options for a given product, and checking
        # if the given option matches any of the existing ones.
        option_ids = list(o.id for o in options)
        other_options = ArrayAgg(Cast(ProductOptionMap.option_id, 'text'))
        having = And(Contains(option_ids, other_options),
                     IsContainedBy(option_ids, other_options))
        data = data.group_by(ProductOptionMap.product_id).having(having)
        return not data.is_empty()

    def add_grid_child(self, options):
        """Create a new product, child of self

        :param options: a list of |grid_option| that the child may have
        """
        assert not self.child_exists(options)

        new_code = Sellable.get_max_value(self.store, Sellable.code)

        child = self.copy_product()
        child.parent = self
        child.sellable.code = next_value_for(new_code)
        Storable(store=self.store, product=child)

        desc_parts = [self.description]
        for option in options:
            desc_parts.append(option.description)
            ProductOptionMap(store=self.store,
                             product=child,
                             attribute=option.attribute,
                             option=option)

        child.sellable.description = u' '.join(desc_parts)

    def update_children_description(self):
        """Update a grid product's children descriptions.

        This method updates all the this product's children description by
        appending the parent description with each grid option description.
        """
        for child in self.children:
            desc_parts = [self.description]
            for opt in child.grid_options:
                desc_parts.append(opt.option.description)
            child.sellable.description = u' '.join(desc_parts)

    def update_children_info(self):
        """Update a grid product's children informations.

        This will update all the children of this product, copying all the
        |sellable| attributes except from the description, which is updated by
        calling the update_children_description method.
        """
        for child in self.children:
            self.copy_product(target=child)
        self.update_children_description()

    def copy_product(self, target=None):
        """This method copies self to another product.

        If the |product| target is None, a new product is created. The copy is
        made by copying all the |sellable| attributes and some of the
        |product| attributes.

        :param target: The |product| target for the copy.
        returns: a |product| similar to self.
        """
        if target is None:
            sellable = self.sellable.copy_sellable()
            target = Product(store=self.store, sellable=sellable)
        else:
            self.sellable.copy_sellable(target=target.sellable)

        props = ['manufacturer', 'brand', 'family', 'width', 'height', 'depth',
                 'weight', 'ncm', 'ex_tipi', 'genero', 'icms_template',
                 'ipi_template', 'pis_template', 'cofins_template']
        for prop in props:
            value = getattr(self, prop)
            setattr(target, prop, value)

        # Since the suppliers are a reference set, we need to copy each object
        # from ProductSupplierInfo
        self._copy_product_suppliers(target)

        return target

    def update_sellable_price(self):
        """Update the sellable price

        Summarize the |product_component| price to set the package price
        """
        if not self.is_package:
            return
        self.sellable.price = sum(child.price * child.quantity
                                  for child in self.get_components())
    #
    # Domain
    #

    def on_create(self):
        ProductCreateEvent.emit(self)

    def on_delete(self):
        ProductRemoveEvent.emit(self)

    def on_update(self):
        store = self.store
        emitted_store_list = getattr(self, '_emitted_store_list', set())

        # Since other classes can propagate this event (like Sellable),
        # emit the event only once for each store.
        if not store in emitted_store_list:
            ProductEditEvent.emit(self)
            emitted_store_list.add(store)

        self._emitted_store_list = emitted_store_list


@implementer(IDescribable)
class GridGroup(Domain):
    """Attributes Group for product grid"""

    __storm_table__ = 'grid_group'

    #: group description
    description = UnicodeCol()

    #: Indicates if grid_group is active
    is_active = BoolCol(allow_none=False, default=True)

    attributes = ReferenceSet('id', 'GridAttribute.group_id')

    #
    # IDescribable
    #

    def get_description(self):
        return self.description

    #
    # Classmethods
    #

    @classmethod
    def get_active_groups(cls, store):
        return store.find(cls, is_active=True)

    @classmethod
    def has_group(cls, store):
        return store.find(cls).any()


class GridAttribute(Domain):
    """Product Attributes for product grid"""

    __storm_table__ = 'grid_attribute'

    #: description of self
    description = UnicodeCol()

    #: Indicates if grid_group is active
    is_active = BoolCol(allow_none=False, default=True)

    #: GridGroup id
    group_id = IdCol()
    group = Reference(group_id, 'GridGroup.id')

    #
    # Public API
    #

    def has_active_options(self):
        """Check if the grid_attribute have active |grid_option|

        :return: ``True`` if self is referenced on any |grid_option|,
        otherwise ``False``
        """
        query = And(GridOption.attribute == self, Eq(GridOption.is_active, True))
        return not self.store.find(GridOption, query).is_empty()


@implementer(IDescribable)
class GridOption(Domain):
    """Attribute options for product grid"""

    __storm_table__ = 'grid_option'

    #: description of self
    description = UnicodeCol()

    #: Indicates if grid_group is active
    is_active = BoolCol(allow_none=False, default=True)

    #: Order that the option will be shown
    option_order = IntCol()

    #: Attribute id for that option
    attribute_id = IdCol()
    attribute = Reference(attribute_id, 'GridAttribute.id')

    #
    # Public API
    #

    def get_description(self):
        return self.description

    def can_remove(self):
        """Check if we can remove the attribute_option from database"""
        return self.store.find(ProductOptionMap, option=self).is_empty()


class ProductAttribute(Domain):
    """Tells what attributes that product have"""

    __storm_table__ = 'product_attribute'

    #: id of the product
    product_id = IdCol()
    product = Reference(product_id, 'Product.id')

    #: id of the attribute
    attribute_id = IdCol()
    attribute = Reference(attribute_id, 'GridAttribute.id')

    #: a list of |grid_option| of the grid_attribute
    options = ReferenceSet('attribute_id', 'GridOption.attribute_id',
                           order_by=('GridOption.option_order',
                                     'GridOption.description'))


class ProductOptionMap(Domain):
    """This class is used to map attribute and options to the product"""

    __storm_table__ = 'product_option_map'

    product_id = IdCol()
    product = Reference(product_id, 'Product.id')

    attribute_id = IdCol()
    attribute = Reference(attribute_id, 'GridAttribute.id')

    option_id = IdCol()
    option = Reference(option_id, 'GridOption.id')


@implementer(IDescribable)
class ProductManufacturer(Domain):
    """Product manufacturer.

    See also:
    `schema <http://doc.stoq.com.br/schema/tables/product_manufacturer.html>`__
    """

    __storm_table__ = 'product_manufacturer'

    #: manufacturer's name
    name = UnicodeCol()

    #: code of the manufacturer
    code = UnicodeCol()

    #
    # IDescribable
    #

    def get_description(self):
        if self.code:
            return _('%s (%s)' % (self.name, self.code))
        return self.name

    def remove(self):
        """Remove this registry from the database."""
        self.store.remove(self)


class ProductHistory(Domain):
    """Stores |product| history, such as sold (via |sale|),
    received (via |receive|), transfered (via |transfer|) and
    decreased quantities.

    See also:
    `schema <http://doc.stoq.com.br/schema/tables/product_history.html>`__

    .. note:: We keep a reference to |sellable| instead of |product| because
              we want to display the sellable id in the interface instead
              of the product id for consistency with interfaces that display
              both.
    """
    __storm_table__ = 'product_history'

    quantity_sold = QuantityCol(default=None)
    quantity_received = QuantityCol(default=None)
    quantity_transfered = QuantityCol(default=None)
    quantity_produced = QuantityCol(default=None)
    quantity_consumed = QuantityCol(default=None)
    quantity_lost = QuantityCol(default=None)
    quantity_decreased = QuantityCol(default=None)
    production_date = DateTimeCol(default=None)
    sold_date = DateTimeCol(default=None)
    received_date = DateTimeCol(default=None)
    decreased_date = DateTimeCol(default=None)

    branch_id = IdCol()

    #: the |branch|
    branch = Reference(branch_id, 'Branch.id')

    sellable_id = IdCol()

    #: the |sellable|
    sellable = Reference(sellable_id, 'Sellable.id')

    @classmethod
    def add_sold_item(cls, store, branch, product_sellable_item):
        """Adds a |saleitem| to the history. *product_sale_item* is an item
        that was created during a |sale|.

        :param store: a store
        :param branch: the |branch|
        :param product_sellable_item: the |saleitem| for the sold |product|
        """
        cls(branch=branch,
            sellable=product_sellable_item.sellable,
            quantity_sold=product_sellable_item.quantity,
            sold_date=TransactionTimestamp(),
            store=store)

    @classmethod
    def add_received_item(cls, store, branch, receiving_order_item):
        """
        Adds a received item, populates the ProductHistory table using a
        *receiving_order_item* created during a |purchase|

        :param store: a store
        :param branch: the |branch|
        :param receiving_order_item: the item received for |purchase|
        """
        cls(branch=branch, sellable=receiving_order_item.sellable,
            quantity_received=receiving_order_item.quantity,
            received_date=receiving_order_item.receiving_order.receival_date,
            store=store)

    @classmethod
    def add_transfered_item(cls, store, branch, transfer_order_item):
        """
        Adds a transfered_item, populates the ProductHistory table using a
        *transfered_order_item* created during a |transfer|.

        :param store: a store
        :param branch: the source branch
        :param transfer_order_item: the item transfered from source branch
        """
        cls(branch=branch, sellable=transfer_order_item.sellable,
            quantity_transfered=transfer_order_item.quantity,
            received_date=transfer_order_item.transfer_order.receival_date,
            store=store)

    @classmethod
    def add_consumed_item(cls, store, branch, consumed_item):
        """
        Adds a consumed_item, populates the ProductHistory table using a
        production_material item that was used in a |production|.

        :param store: a store
        :param branch: the source branch
        :param retained_item: a ProductionMaterial instance
        """
        cls(branch=branch, sellable=consumed_item.product.sellable,
            quantity_consumed=consumed_item.consumed,
            production_date=localtoday(),
            store=store)

    @classmethod
    def add_produced_item(cls, store, branch, produced_item):
        """
        Adds a produced_item, populates the ProductHistory table using a
        production_item that was produced in a production order.

        :param store: a store
        :param branch: the source branch
        :param retained_item: a ProductionItem instance
        """
        cls(branch=branch, sellable=produced_item.product.sellable,
            quantity_produced=produced_item.produced,
            production_date=localtoday(), store=store)

    @classmethod
    def add_lost_item(cls, store, branch, lost_item):
        """
        Adds a lost_item, populates the ProductHistory table using a
        production_item/product_material that was lost in a production order.

        :param store: a store
        :param branch: the source branch
        :param lost_item: a ProductionItem or ProductionMaterial instance
        """
        if lost_item.lost <= 0:
            raise ValueError("lost_item must have a positive lost attribute")

        cls(branch=branch, sellable=lost_item.product.sellable,
            quantity_lost=lost_item.lost,
            production_date=localtoday(), store=store)

    @classmethod
    def add_decreased_item(cls, store, branch, item):
        """
        Adds a decreased item, populates the ProductHistory table informing
        how many items wore manually decreased from stock.

        :param store: a store
        :param branch: the source |branch|
        :param item: a StockDecreaseItem instance
        """
        cls(branch=branch, sellable=item.sellable,
            quantity_decreased=item.quantity,
            decreased_date=localtoday(),
            store=store)


class ProductStockItem(Domain):
    """Class that makes a reference to the |product| stock of a
    certain |branch|.

    See also:
    `schema <http://doc.stoq.com.br/schema/tables/product_stock_item.html>`__
    """

    __storm_table__ = 'product_stock_item'

    #: the average stock price, will be updated as new stock items are
    #: received.
    stock_cost = PriceCol(default=0)

    #: number of storables in the stock item
    quantity = QuantityCol(default=0)

    branch_id = IdCol()

    #: the |branch| this stock item belongs to
    branch = Reference(branch_id, 'Branch.id')

    storable_id = IdCol()

    #: the |storable| the stock item refers to
    storable = Reference(storable_id, 'Storable.id')

    batch_id = IdCol()

    #: The |batch| that the storable is in.
    batch = Reference(batch_id, 'StorableBatch.id')

    @property
    def transactions(self):
        return self.store.find(StockTransactionHistory,
                               storable=self.storable,
                               branch=self.branch,
                               batch=self.batch)


class Storable(Domain):
    '''Storable represents the stock of a |product|.

    The actual stock of an item is in ProductStockItem.

    See also:
    `schema <http://doc.stoq.com.br/schema/tables/storable.html>`__
    '''

    __storm_table__ = 'storable'

    #: the |product| the stock represents
    product = Reference('id', 'Product.id')

    #: If this storable should have a finer grain control by batches. When this
    #: is true, stock for this storable will also require a batch information.
    #: This will allow us to control from what batch a sale item came from, and
    #: it will also let us know from what purchase this batch came from.
    is_batch = BoolCol(default=False)

    #: minimum quantity of stock items allowed
    minimum_quantity = QuantityCol(default=0)

    #: maximum quantity of stock items allowed
    maximum_quantity = QuantityCol(default=0)

    def __init__(self, **kwargs):
        assert 'product' in kwargs
        kwargs['id'] = kwargs['product'].id

        super(Storable, self).__init__(**kwargs)

    #
    #  Classmethods
    #

    @classmethod
    def get_initial_stock_data(cls, store, branch):
        """Get data about |storables| without a |productstockitem|

        This will get all sellables, products and storables that dont have a
        |productstockitem| on the given branch.

        :param store: the store used to query the storables
        :param branch: the |branch| used to check for the stock item existence
        :returns: a result set of |sellable|, |product| and |storable|
        """
        tables = [
            Sellable,
            Join(Product, Product.id == Sellable.id),
            Join(Storable, Storable.id == Product.id),
            LeftJoin(ProductStockItem,
                     And(ProductStockItem.storable_id == cls.id,
                         ProductStockItem.branch_id == branch.id))
        ]
        query = Eq(ProductStockItem.id, None)

        return store.using(*tables).find((Sellable, Product, Storable), query)

    #
    #  Public API
    #

    def increase_stock(self, quantity, branch, type, object_id, unit_cost=None,
                       batch=None):
        """When receiving a product, update the stock reference for this new
        item on a specific |branch|.

        :param quantity: amount to increase
        :param branch: |branch| that stores the stock
        :param type: the type of the stock increase. One of the
            StockTransactionHistory.types
        :param object_id: the id of the object responsible for the transaction
        :param unit_cost: unit cost of the new stock or `None`
        :param batch: The batch of the storable. Should be not ``None`` if
            self.is_batch is ``True``
        """
        if quantity <= 0:
            raise ValueError(_(u"quantity must be a positive number"))
        if branch is None:
            raise ValueError(u"branch cannot be None")

        stock_item = self.get_stock_item(branch, batch)
        old_quantity = stock_item.quantity if stock_item else 0

        stock_transaction = StockTransactionHistory(
            store=self.store,
            storable=self,
            branch=branch,
            batch=batch,
            quantity=quantity,
            unit_cost=unit_cost,
            responsible=get_current_user(self.store),
            type=type,
            object_id=object_id)
        stock_item = stock_transaction.product_stock_item

        ProductStockUpdateEvent.emit(self.product, branch, old_quantity,
                                     stock_item.quantity)

    def decrease_stock(self, quantity, branch, type, object_id,
                       cost_center=None, batch=None):
        """When receiving a product, update the stock reference for the sold item
        this on a specific |branch|. Returns the stock item that was
        decreased.

        :param quantity: amount to decrease
        :param branch: a |branch|
        :param type: the type of the stock increase. One of the
            StockTransactionHistory.types
        :param object_id: the id of the object responsible for the transaction
        :param cost_center: the |costcenter| to which this stock decrease is
            related, if any
        :param batch: The batch of the storable. Should be not ``None`` if
            self.is_batch is ``True``
        """
        # FIXME: Put this back once 1.6 is released
        # assert isinstance(type, int)

        if quantity <= 0:
            raise ValueError(_(u"quantity must be a positive number"))
        if branch is None:
            raise ValueError(u"branch cannot be None")

        stock_item = self.get_stock_item(branch, batch)
        if stock_item is None or quantity > stock_item.quantity:
            raise StockError(
                _('Quantity to sell is greater than the available stock.'))

        old_quantity = stock_item.quantity
        stock_transaction = StockTransactionHistory(
            store=self.store,
            storable=self,
            branch=branch,
            batch=batch,
            quantity=-quantity,
            unit_cost=stock_item.stock_cost,
            responsible=get_current_user(self.store),
            type=type,
            object_id=object_id)

        if cost_center is not None:
            cost_center.add_stock_transaction(stock_transaction)

        ProductStockUpdateEvent.emit(self.product, branch, old_quantity,
                                     stock_item.quantity)

        return stock_item

    def register_initial_stock(self, quantity, branch, unit_cost,
                               batch_number=None):
        """Register initial stock, by increasing the amount of this storable,
        for the given quantity and |branch|

        :param quantity: The inital stock quantity for this storable
        :param branch: The branch where the given quantity is avaiable for this
          storable
        :param unit_cost: The unitary cost for the initial stock
        :param batch_number: a batch number that will be used to
            get or create a |batch| it will be get from the item's
            pending quantity. Must be ``None`` if the :obj:`.is_batch`
            is ``False``.
        """
        if batch_number is not None:
            batch = StorableBatch.get_or_create(
                self.store,
                storable=self,
                batch_number=batch_number)
        else:
            batch = None

        self.increase_stock(quantity, branch,
                            StockTransactionHistory.TYPE_INITIAL,
                            object_id=None, unit_cost=unit_cost, batch=batch)

    def update_stock_cost(self, stock_cost, branch, batch=None):
        """Update the stock cost

        :param stock_cost: The new stock cost
        :param branch: The branch where the stock cost will be updated
        :param batch: The batch of the storable
            self.is_batch is ``True``
        """
        StockTransactionHistory(
            store=self.store,
            storable=self,
            branch=branch,
            batch=batch,
            quantity=0,
            unit_cost=stock_cost,
            responsible=get_current_user(self.store),
            type=StockTransactionHistory.TYPE_UPDATE_STOCK_COST,
            object_id=None)

    def get_total_balance(self):
        """Return the stock balance for the |product| in all |branches|

        :returns: the amount of stock available in all |branches|
        """
        stock_items = self.get_stock_items()
        return stock_items.sum(ProductStockItem.quantity) or Decimal(0)

    def get_balance_for_branch(self, branch):
        """Return the stock balance for the |product| in a |branch|. If this
        storable have batches, the balance for all batches will be returned.

        If you want the balance for a specific |batch|, the

        :param branch: the |branch| to get the stock balance for
        :returns: the amount of stock available in the |branch|
        """
        store = self.store
        stock_items = store.find(ProductStockItem, storable=self,
                                 branch=branch)
        return stock_items.sum(ProductStockItem.quantity) or Decimal(0)

    def get_stock_items(self):
        """Fetches the stock items available for all |branches|.

        :returns: a sequence of stock items
        """
        return self.store.find(ProductStockItem, storable=self)

    def get_stock_item(self, branch, batch):
        """Fetches the stock item for the given |branch|, |batch| and this
        |storable|.

        :param branch: the |branch| to get the stock item for
        :param batch: the |batch| to get the stock item for
        :returns: a stock item
        """
        self.validate_batch(batch, sellable=self.product.sellable)
        return self.store.find(ProductStockItem, branch=branch, storable=self,
                               batch=batch).one()

    def get_available_batches(self, branch):
        """Return all batches that have some stock left in the given branch

        :param branch: the |branch| that we are getting the avaiable batches
        :returns: all batches available for this storable in the given branch
        """
        tables = [StorableBatch,
                  LeftJoin(ProductStockItem,
                           And(ProductStockItem.storable_id == StorableBatch.storable_id,
                               ProductStockItem.batch_id == StorableBatch.id))]
        query = And(ProductStockItem.storable_id == self.id,
                    ProductStockItem.branch_id == branch.id,
                    ProductStockItem.quantity > 0)
        return self.store.using(*tables).find(StorableBatch, query)


# TODO: Add a reference to the batch in:
# * References sellable:
#     - Maybe: ProductHistory
# * References product:
#     - ProductionMaterial: This is not that simple and will require some
#       refatoring in the production process
#     - ProductionProducedItem (Maybe)

@implementer(IDescribable)
class StorableBatch(Domain):
    """Batch information for storables.

    A batch is a colection of products (storable) that were produced at the same
    time and thus they have some common information, such as expiration date.

    This information is useful since sometimes its necessary to make decisions
    based on the batch like a special promotion for older batches (if it is
    close to the expiration date, for instance) or if a batch is somehow
    defective and we need to contact the clients that purchased items from this
    batch.
    """

    __storm_table__ = 'storable_batch'

    #: The sequence number for this batch. Should be unique for a given
    #: storable
    batch_number = UnicodeCol(allow_none=False)

    #: The date this batch was created
    create_date = DateTimeCol(default_factory=localnow)

    #: An expiration date, specially for perishable products, like milk and food in
    #: general
    expire_date = DateTimeCol()

    #: Some space for the users to add notes to this batch.
    notes = UnicodeCol()

    storable_id = IdCol(allow_none=False)

    #: The storable that is in this batch
    storable = Reference(storable_id, 'Storable.id')

    #
    #  IDescribable
    #

    def get_description(self):
        return self.batch_number

    #
    #  Classmethods
    #

    @classmethod
    def is_batch_number_available(cls, store, batch_number,
                                  exclude_storable=None):
        """Test if batch_number is available

        Useful to find if a batch number is available to be used on a
        new |batch|.

        If you are increasing the stock of a storable, you probably
        want to allow an existing batch number for it, in this case,
        you can use exclude_storable param for that.

        :param store: a store
        :param batch_number: the batch number to check for availability
        :param exclude_storable: if not ``None``, the |storable| to
            exclude from the test
        """
        query = cls.batch_number == batch_number
        if exclude_storable is not None:
            query = And(query, cls.storable_id != exclude_storable.id)

        return store.find(cls, query).is_empty()

    @classmethod
    def get_max_batch_number(cls, store):
        attr = SplitPart(cls.batch_number, u'-', 1)
        return StorableBatch.get_max_value(store, attr, validate_attr=False)

    #
    #  Public API
    #

    def get_balance_for_branch(self, branch):
        """Return the stock balance for this |batch| in a |branch|.

        :param branch: the |branch| to get the stock balance for
        :returns: the amount of stock available in the |branch|
        """
        store = self.store
        stock_items = store.find(ProductStockItem, storable=self.storable,
                                 batch=self, branch=branch)
        return stock_items.sum(ProductStockItem.quantity) or Decimal(0)


class StockTransactionHistory(Domain):
    """ This class stores information about all transactions made in the
    stock

    Everytime a |storable| has its stock increased or decreased, an object of
    this class will be created, registering the quantity, cost, responsible and
    reason for the transaction
    """

    __storm_table__ = 'stock_transaction_history'

    #: the transaction is an initial stock adustment. Note that with this
    #: transaction, there is no related object.
    TYPE_INITIAL = u'initial'

    #: the transaction is a sale
    TYPE_SELL = u'sell'

    #: the transaction is a return of a sale
    TYPE_RETURNED_SALE = u'returned-sale'

    #: the transaction is an undo of a returned sale
    TYPE_UNDO_RETURNED_SALE = u'undo-returned-sale'

    #: the transaction is the cancellation of a sale
    TYPE_CANCELED_SALE = u'cancelled-sale'

    #: the transaction is the receival of a purchase
    TYPE_RECEIVED_PURCHASE = u'received-purchase'

    #: the transaction is the return of a loan
    TYPE_RETURNED_LOAN = u'returned-loan'

    #: the transaction is a loan
    TYPE_LOANED = u'loan'

    #: the transaction is the allocation of a product to a production
    TYPE_PRODUCTION_ALLOCATED = u'production-allocated'

    #: the transaction is the production of a product
    TYPE_PRODUCTION_PRODUCED = u'production-produced'

    #: the transaction is the return of an item from a production
    TYPE_PRODUCTION_RETURNED = u'production-returned'

    #: the transaction is a stock decrease
    TYPE_STOCK_DECREASE = u'stock-decrease'

    #: the transaction is a transfer from a branch
    TYPE_TRANSFER_FROM = u'transfer-from'

    #: the transaction is a transfer to a branch
    TYPE_TRANSFER_TO = u'transfer-to'

    #: the transaction is the adjustment of an inventory
    TYPE_INVENTORY_ADJUST = u'inventory-adjust'

    #: the transaction is the production of a product that didn't enter
    #: stock right after its creation
    TYPE_PRODUCTION_SENT = u'production-sent'

    #: this transaction was created automatically by an upgrade from a previous
    #: version of Stoq, when this history didn't exist.
    TYPE_IMPORTED = u'imported'

    #: the transaction is the return of a product to another company (ie, this
    #: shop is giving the product back to the other company).
    TYPE_CONSIGNMENT_RETURNED = u'consignment-returned'

    #: the transaction is the utilization of a
    #: |product| on a |workorderitem|
    TYPE_WORK_ORDER_USED = u'wo-used'

    #: the transaction is the return of a |product| on a
    #: |workorderitem| to the stock
    TYPE_WORK_ORDER_RETURN_TO_STOCK = u'wo-returned-to-stock'

    #: the transaction is a reserved product from a sale
    TYPE_SALE_RESERVED = u'sale-reserved'

    #: the transaction is a reserved product from a sale
    TYPE_SALE_RETURN_TO_STOCK = u'sale-return-to-stock'

    #: the transaction is a manual adjust done on the database
    TYPE_MANUAL_ADJUST = u'manual-adjust'

    #: the transaction is an adjustment on the stock cost with no update
    #: on the stock itself
    TYPE_UPDATE_STOCK_COST = u'update-stock-cost'

    types = {TYPE_INVENTORY_ADJUST: _(u'Adjustment for inventory %s'),
             TYPE_RETURNED_LOAN: _(u'Returned from loan %s'),
             TYPE_LOANED: _(u'Loaned for loan %s'),
             TYPE_PRODUCTION_ALLOCATED: _(u'Allocated for production %s'),
             TYPE_PRODUCTION_PRODUCED: _(u'Produced in production %s'),
             TYPE_PRODUCTION_SENT: _(u'Produced in production %s'),
             TYPE_PRODUCTION_RETURNED: _(u'Returned remaining from '
                                         u'production %s'),
             TYPE_RECEIVED_PURCHASE: _(u'Received for receiving order %s'),
             TYPE_RETURNED_SALE: _(u'Returned sale %s'),
             TYPE_UNDO_RETURNED_SALE: _(u'Undone the returned sale %s'),
             TYPE_CANCELED_SALE: _(u'Returned from canceled sale %s'),
             TYPE_SELL: _(u'Sold in sale %s'),
             TYPE_STOCK_DECREASE: _(u'Product removal for stock decrease %s'),
             TYPE_TRANSFER_FROM: _(u'Transfered from branch in transfer '
                                   u'order %s'),
             TYPE_TRANSFER_TO: _(u'Transfered to this branch in transfer '
                                 u'order %s'),
             TYPE_INITIAL: _(u'Registred initial stock'),
             TYPE_IMPORTED: _(u'Imported from previous version'),
             TYPE_CONSIGNMENT_RETURNED: _(u'Consigned product returned %s.'),
             TYPE_WORK_ORDER_USED: _(u'Used on work order %s.'),
             TYPE_WORK_ORDER_RETURN_TO_STOCK: _(u'Returned to stock on work order %s.'),
             TYPE_SALE_RESERVED: _(u'Reserved for sale %s.'),
             TYPE_SALE_RETURN_TO_STOCK: _(u'Reserved quantity for sale %s '
                                          u'returned to stock.'),
             TYPE_MANUAL_ADJUST: _(u'Quantity manually adjusted'),
             TYPE_UPDATE_STOCK_COST: _(u'Stock cost updated with no change on the stock'),
             }

    #: the date and time the transaction was made
    date = DateTimeCol(default_factory=localnow)

    branch_id = IdCol(allow_none=False)
    branch = Reference(branch_id, 'Branch.id')

    storable_id = IdCol(allow_none=False)
    storable = Reference(storable_id, 'Storable.id')

    batch_id = IdCol()
    batch = Reference(batch_id, 'StorableBatch.id')

    unit_cost = PriceCol(default=None)

    #: the stock cost of the transaction on the time it was made
    stock_cost = PriceCol()

    #: The quantity that was removed or added to the stock.
    #: Positive value if the value was increased, negative if decreased.
    quantity = QuantityCol()

    responsible_id = IdCol()

    #: the |loginuser| responsible for the transaction
    responsible = Reference(responsible_id, 'LoginUser.id')

    #: the id of the object who altered the stock
    object_id = IdCol()

    #: the type of the transaction
    type = EnumCol(allow_none=False, default=TYPE_INITIAL)

    @property
    def total(self):
        return currency(abs(self.stock_cost * self.quantity))

    @property
    def product_stock_item(self):
        return self.storable.get_stock_item(self.branch, self.batch)

    def __init__(self, **kwargs):
        # In some situations, storm would create the object without passing the
        # id of those reference objects, making the trigger fail to execute.
        # batch is the only one that we check differently because it is
        # not mandatory
        if 'branch_id' not in kwargs:
            kwargs['branch_id'] = kwargs.pop('branch').id
        if 'storable_id' not in kwargs:
            kwargs['storable_id'] = kwargs.pop('storable').id
        if 'batch' in kwargs:
            batch = kwargs.pop('batch')
            kwargs['batch_id'] = batch and batch.id

        super(StockTransactionHistory, self).__init__(**kwargs)

        # Flush the store so the trigger that updates the ProductStockItem
        # will run and reload it after
        self.store.flush()
        autoreload_object(self, obj_store=True)
        autoreload_object(self.product_stock_item, obj_store=True)

    def get_object(self):
        if self.type in [self.TYPE_INITIAL, self.TYPE_IMPORTED,
                         self.TYPE_UPDATE_STOCK_COST, self.TYPE_MANUAL_ADJUST]:
            return None
        elif self.type in [self.TYPE_SELL, self.TYPE_CANCELED_SALE,
                           self.TYPE_SALE_RESERVED]:
            from stoqlib.domain.sale import SaleItem
            return self.store.get(SaleItem, self.object_id)
        elif self.type in [self.TYPE_RETURNED_SALE,
                           self.TYPE_UNDO_RETURNED_SALE]:
            from stoqlib.domain.returnedsale import ReturnedSaleItem
            return self.store.get(ReturnedSaleItem, self.object_id)
        elif self.type == self.TYPE_PRODUCTION_PRODUCED:
            from stoqlib.domain.production import ProductionItem
            return self.store.get(ProductionItem, self.object_id)
        elif self.type in [self.TYPE_PRODUCTION_ALLOCATED,
                           self.TYPE_PRODUCTION_RETURNED]:
            from stoqlib.domain.production import ProductionMaterial
            return self.store.get(ProductionMaterial, self.object_id)
        elif self.type == self.TYPE_RECEIVED_PURCHASE:
            from stoqlib.domain.receiving import ReceivingOrderItem
            return self.store.get(ReceivingOrderItem, self.object_id)
        elif self.type in [self.TYPE_RETURNED_LOAN, self.TYPE_LOANED]:
            from stoqlib.domain.loan import LoanItem
            return self.store.get(LoanItem, self.object_id)
        elif self.type == self.TYPE_STOCK_DECREASE:
            from stoqlib.domain.stockdecrease import StockDecreaseItem
            return self.store.get(StockDecreaseItem, self.object_id)
        elif self.type in [self.TYPE_TRANSFER_FROM, self.TYPE_TRANSFER_TO]:
            from stoqlib.domain.transfer import TransferOrderItem
            return self.store.get(TransferOrderItem, self.object_id)
        elif self.type == self.TYPE_INVENTORY_ADJUST:
            from stoqlib.domain.inventory import InventoryItem
            return self.store.get(InventoryItem, self.object_id)
        elif self.type == self.TYPE_PRODUCTION_SENT:
            from stoqlib.domain.production import ProductionProducedItem
            return self.store.get(ProductionProducedItem, self.object_id)
        elif self.type == self.TYPE_CONSIGNMENT_RETURNED:
            from stoqlib.domain.purchase import PurchaseItem
            return self.store.get(PurchaseItem, self.object_id)
        elif self.type in [self.TYPE_WORK_ORDER_USED,
                           self.TYPE_WORK_ORDER_RETURN_TO_STOCK]:
            from stoqlib.domain.workorder import WorkOrderItem
            return self.store.get(WorkOrderItem, self.object_id)
        else:  # pragma: nocoverage
            raise NotImplementedError(self.type)

    def get_object_parent(self):
        obj = self.get_object()
        if not obj:
            return None

        from stoqlib.domain.inventory import InventoryItem
        from stoqlib.domain.loan import LoanItem
        from stoqlib.domain.production import ProductionItem
        from stoqlib.domain.production import ProductionMaterial
        from stoqlib.domain.production import ProductionProducedItem
        from stoqlib.domain.purchase import PurchaseItem
        from stoqlib.domain.receiving import ReceivingOrderItem
        from stoqlib.domain.returnedsale import ReturnedSaleItem
        from stoqlib.domain.sale import SaleItem
        from stoqlib.domain.stockdecrease import StockDecreaseItem
        from stoqlib.domain.workorder import WorkOrderItem
        from stoqlib.domain.transfer import TransferOrderItem

        if isinstance(obj, SaleItem):
            return obj.sale
        elif isinstance(obj, ReturnedSaleItem):
            return obj.returned_sale
        elif isinstance(obj, ProductionItem):
            return obj.order
        elif isinstance(obj, ProductionProducedItem):
            return obj.order
        elif isinstance(obj, ProductionMaterial):
            return obj.order
        elif isinstance(obj, ReceivingOrderItem):
            return obj.receiving_order
        elif isinstance(obj, LoanItem):
            return obj.loan
        elif isinstance(obj, StockDecreaseItem):
            return obj.stock_decrease
        elif isinstance(obj, TransferOrderItem):
            return obj.transfer_order
        elif isinstance(obj, InventoryItem):
            return obj.inventory
        elif isinstance(obj, PurchaseItem):
            return obj.order
        elif isinstance(obj, WorkOrderItem):
            return obj.order
        else:  # pragma: nocoverage
            raise NotImplementedError(obj)

    def get_description(self):
        """ Based on the type of the transaction, returns the string
        description
        """
        if self.type in [self.TYPE_INITIAL, self.TYPE_IMPORTED,
                         self.TYPE_MANUAL_ADJUST, self.TYPE_UPDATE_STOCK_COST]:
            return self.types[self.type]

        object_parent = self.get_object_parent()
        number = unicode(object_parent.identifier)

        return self.types[self.type] % number


class ProductComponent(Domain):
    """A |product| and it's related |component| eg other product

    See also:
    `schema <http://doc.stoq.com.br/schema/tables/product_component.html>`__
    """

    __storm_table__ = 'product_component'

    quantity = QuantityCol(default=Decimal(1))
    product_id = IdCol()
    product = Reference(product_id, 'Product.id')
    component_id = IdCol()
    component = Reference(component_id, 'Product.id')
    design_reference = UnicodeCol(default=u'')
    #: The price to be used on |sale_item|
    price = PriceCol()


@implementer(IDescribable)
class ProductQualityTest(Domain):
    """A quality test that a manufactured product will be submitted to.

    See also:
    `schema <http://doc.stoq.com.br/schema/tables/product_quality_test.html>`__
    """

    __storm_table__ = 'product_quality_test'

    TYPE_BOOLEAN = u'boolean'
    TYPE_DECIMAL = u'decimal'

    types = {
        TYPE_BOOLEAN: _(u'Boolean'),
        TYPE_DECIMAL: _(u'Decimal'),
    }

    product_id = IdCol()
    product = Reference(product_id, 'Product.id')
    test_type = EnumCol(allow_none=False, default=TYPE_BOOLEAN)
    description = UnicodeCol(default=u'')
    notes = UnicodeCol(default=u'')
    success_value = UnicodeCol(default=u'True')

    def get_description(self):
        return self.description

    @property
    def type_str(self):
        return self.types[self.test_type]

    @property
    def success_value_str(self):
        return _(self.success_value)

    def get_boolean_value(self):
        assert self.test_type == self.TYPE_BOOLEAN
        if self.success_value == u'True':
            return True
        elif self.success_value == u'False':
            return False
        else:  # pragma: nocoverage
            raise ValueError(self.success_value)

    def get_range_value(self):
        assert self.test_type == self.TYPE_DECIMAL
        a, b = self.success_value.split(u' - ')
        return Decimal(a), Decimal(b)

    def set_boolean_value(self, value):
        self.success_value = unicode(value)

    def set_range_value(self, min_value, max_value):
        self.success_value = u'%s - %s' % (min_value, max_value)

    def result_value_passes(self, value):
        if self.test_type == self.TYPE_BOOLEAN:
            return self.get_boolean_value() == value
        else:
            a, b = self.get_range_value()
            return a <= value <= b


_StockSummary = Alias(Select(
    columns=[
        ProductStockItem.batch_id,
        ProductStockItem.branch_id,
        Alias(Sum(ProductStockItem.quantity), 'stock')],
    tables=[
        ProductStockItem],
    group_by=[
        ProductStockItem.batch_id,
        ProductStockItem.branch_id]),
    '_stock_summary')


class StorableBatchView(Viewable):
    """A view for |batches|

    This is used to get the most information of a |batch|
    without doing lots of database queries.

    It's bestly used with :meth:`.find_by_storable`
    """

    #: the |batch| object
    batch = StorableBatch

    #: the |branch| this batch is in
    branch = Branch

    # StorableBatch
    id = StorableBatch.id
    create_date = StorableBatch.create_date
    batch_number = StorableBatch.batch_number
    stock = Coalesce(Field('_stock_summary', 'stock'), 0)

    tables = [
        StorableBatch,
        LeftJoin(_StockSummary,
                 Field('_stock_summary', 'batch_id') == StorableBatch.id),
        LeftJoin(Branch, Field('_stock_summary', 'branch_id') == Branch.id),
    ]

    @classmethod
    def find_by_storable(cls, store, storable, branch=None):
        """Find results for this view that for *storable*

        Normally it's best to use this instead of *store.find* since
        it'll only |batches| for the given |storable|.

        :param store: the store that will be used to find the results
        :param storable: the |storable| used to filter the results
        :param branch: a |branch| that, if not ``None``, will be used to
            filter the results to only get batches on that branch.
        :returns: the matching views
        :rtype: a sequence of :class:`StorableBatchView`
        """
        query = StorableBatch.storable_id == storable.id
        if branch is not None:
            query = And(query,
                        Field('_stock_summary', 'branch_id') == branch.id)
        return store.find(cls, query)

    @classmethod
    def find_available_by_storable(cls, store, storable, branch=None):
        """Find results for this view that for *storable* that have stock

        The same as :meth:`.find_by_storable`, but only results with
        :obj:`.stock` > 0 will be fetched

        :param store: the store that will be used to find the results
        :param storable: the |storable| used to filter the results
        :param branch: a |branch| that, if not ``None``, will be used to
            filter the results to only get batches on that branch.
        :returns: the matching views
        :rtype: a sequence of :class:`StorableBatchView`
        """
        results = cls.find_by_storable(store, storable, branch=branch)
        return results.find(Field('_stock_summary', 'stock') > 0)
