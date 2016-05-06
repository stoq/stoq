# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2009-2013 Async Open Source <http://www.async.com.br>
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
##
""" Base classes to manage production informations """

# pylint: enable=E1101

import collections
from decimal import Decimal

from storm.expr import And, Join
from storm.references import Reference, ReferenceSet
from zope.interface import implementer

from stoqlib.database.properties import (UnicodeCol, DateTimeCol, IntCol,
                                         QuantityCol, BoolCol, IdentifierCol,
                                         IdCol, EnumCol)
from stoqlib.database.viewable import Viewable
from stoqlib.domain.base import Domain
from stoqlib.domain.product import ProductHistory, StockTransactionHistory
from stoqlib.domain.interfaces import IContainer, IDescribable
from stoqlib.lib.dateutils import localnow, localtoday
from stoqlib.lib.translation import stoqlib_gettext


_ = stoqlib_gettext


@implementer(IContainer)
@implementer(IDescribable)
class ProductionOrder(Domain):
    """Production Order object implementation.
    """

    __storm_table__ = 'production_order'

    #: The production order is opened, production items might have been added.
    ORDER_OPENED = u'opened'

    #: The production order is waiting some conditions to start the
    #: manufacturing process.
    ORDER_WAITING = u'waiting'

    #: The production order have already started.
    ORDER_PRODUCING = u'producing'

    #: The production is in quality assurance phase.
    ORDER_QA = u'quality-assurance'

    #: The production have finished.
    ORDER_CLOSED = u'closed'

    #: Production cancelled
    ORDER_CANCELLED = u'cancelled'

    statuses = collections.OrderedDict([
        (ORDER_OPENED, _(u'Opened')),
        (ORDER_WAITING, _(u'Waiting')),
        (ORDER_PRODUCING, _(u'Producing')),
        (ORDER_QA, _(u'Quality Assurance')),
        (ORDER_CLOSED, _(u'Closed')),
        (ORDER_CANCELLED, _(u'Cancelled')),
    ])

    #: A numeric identifier for this object. This value should be used instead of
    #: :obj:`Domain.id` when displaying a numerical representation of this object to
    #: the user, in dialogs, lists, reports and such.
    identifier = IdentifierCol()

    #: the production order status
    status = EnumCol(allow_none=False, default=ORDER_OPENED)

    #: the date when the production order was created
    open_date = DateTimeCol(default_factory=localnow)

    #: the date when the production order have been closed
    close_date = DateTimeCol(default=None)

    #: the date when the production order have been cancelled
    cancel_date = DateTimeCol(default=None)

    #: the production order description
    description = UnicodeCol(default=u'')

    expected_start_date = DateTimeCol(default=None)

    start_date = DateTimeCol(default=None)

    responsible_id = IdCol(default=None)

    #: the person responsible for the production order
    responsible = Reference(responsible_id, 'Employee.id')

    branch_id = IdCol()

    #: branch this production belongs to
    branch = Reference(branch_id, 'Branch.id')

    produced_items = ReferenceSet('id', 'ProductionProducedItem.order_id')

    #
    # IContainer implmentation
    #

    def get_items(self):
        return self.store.find(ProductionItem, order=self)

    def add_item(self, sellable, quantity=Decimal(1)):
        return ProductionItem(order=self, product=sellable.product,
                              quantity=quantity,
                              store=self.store)

    def remove_item(self, item):
        assert isinstance(item, ProductionItem)
        if item.order is not self:
            raise ValueError(_(u'Argument item must have an order attribute '
                               u'associated with the current production '
                               u'order instance.'))
        item.order = None
        self.store.maybe_remove(item)

    #
    # Public API
    #

    def can_cancel(self):
        """Checks if this order can be cancelled

        Only orders that didn't start yet can be canceled, this means
        only opened and waiting productions.
        """
        return self.status in [self.ORDER_OPENED,
                               self.ORDER_WAITING]

    def can_finalize(self):
        """Checks if this order can be finalized

        Only orders that didn't start yet can be canceled, this means
        only producing and waiting qa productions.
        """
        return self.status in [self.ORDER_PRODUCING,
                               self.ORDER_QA]

    def get_service_items(self):
        """Returns all the services needed by this production.

        :returns: a sequence of :class:`ProductionService` instances.
        """
        return self.store.find(ProductionService, order=self)

    def remove_service_item(self, item):
        assert isinstance(item, ProductionService)
        if item.order is not self:
            raise ValueError(_(u'Argument item must have an order attribute '
                               u'associated with the current production '
                               u'order instance.'))
        item.order = None
        self.store.maybe_remove(item)

    def get_material_items(self):
        """Returns all the material needed by this production.

        :returns: a sequence of :class:`ProductionMaterial` instances.
        """
        return self.store.find(ProductionMaterial, order=self,
                               )

    def start_production(self):
        """Start the production by allocating all the material needed.
        """
        assert self.status in [ProductionOrder.ORDER_OPENED,
                               ProductionOrder.ORDER_WAITING]

        for material in self.get_material_items():
            material.allocate()

        self.start_date = localtoday()
        self.status = ProductionOrder.ORDER_PRODUCING

    def cancel(self):
        """Cancel the production when this is Open or Waiting.
        """
        assert self.can_cancel()
        self.status = self.ORDER_CANCELLED
        self.cancel_date = localtoday()

    def is_completely_produced(self):
        return all(i.is_completely_produced() for i in self.get_items())

    def is_completely_tested(self):
        # Produced items are only stored if there are quality tests for this
        # product
        produced_items = list(self.produced_items)
        if not produced_items:
            return True

        return all([item.test_passed for item in produced_items])

    def try_finalize_production(self, ignore_completion=False):
        """When all items are completely produced, change the status of the
        production to CLOSED.
        """
        assert self.can_finalize(), self.status

        if ignore_completion:
            is_produced = True
        else:
            is_produced = self.is_completely_produced()
        is_tested = self.is_completely_tested()

        if is_produced and not is_tested:
            # Fully produced but not fully tested. Keep status as QA
            self.status = ProductionOrder.ORDER_QA
        elif is_produced and is_tested:
            # All items must be completely produced and tested
            self.close_date = localtoday()
            self.status = ProductionOrder.ORDER_CLOSED

        # If the order is closed, return the the remaining allocated material to
        # the stock
        if self.status == ProductionOrder.ORDER_CLOSED:
            # Return remaining allocated material to the stock
            for m in self.get_material_items():
                m.return_remaining()

            # Increase the stock for the produced items
            for p in self.produced_items:
                p.send_to_stock()

    def set_production_waiting(self):
        assert self.status == ProductionOrder.ORDER_OPENED

        self.status = ProductionOrder.ORDER_WAITING

    def get_status_string(self):
        return ProductionOrder.statuses[self.status]

    def get_branch_name(self):
        return self.branch.get_description()

    def get_responsible_name(self):
        if self.responsible is not None:
            return self.responsible.person.name
        return u''

    #
    # IDescribable implementation
    #

    def get_description(self):
        return self.description


@implementer(IDescribable)
class ProductionItem(Domain):
    """Production Item object implementation.
    """

    __storm_table__ = 'production_item'

    #: The product's quantity that will be manufactured.
    quantity = QuantityCol(default=1)

    #: The product's quantity that was manufactured.
    produced = QuantityCol(default=0)

    #: The product's quantity that was lost.
    lost = QuantityCol(default=0)

    order_id = IdCol()

    #: The :class:`ProductionOrder` of this item.
    order = Reference(order_id, 'ProductionOrder.id')

    product_id = IdCol()

    #: The product that will be manufactured.
    product = Reference(product_id, 'Product.id')

    def get_description(self):
        return self.product.sellable.get_description()

    #
    # Properties
    #

    @property
    def unit_description(self):
        return self.product.sellable.unit_description

    @property
    def sellable(self):
        return self.product.sellable

    #
    # Private API
    #

    def _get_material_from_component(self, component):
        store = self.store
        return store.find(ProductionMaterial, product=component.component,
                          order=self.order).one()

    #
    # Public API
    #

    def get_components(self):
        return self.product.get_components()

    def can_produce(self, quantity):
        """Returns if we can produce a certain quantity.  We can produce a
        quantity items until we reach the total quantity that will be
        manufactured minus the quantity that was lost.

        :param quantity: the quantity that will be produced.
        """
        assert quantity > 0
        if self.order.status != ProductionOrder.ORDER_PRODUCING:
            return False

        return self.produced + quantity + self.lost <= self.quantity

    def is_completely_produced(self):
        return self.quantity == self.produced + self.lost

    def produce(self, quantity, produced_by=None, serials=None):
        """Sets a certain quantity as produced. The quantity will be marked as
        produced only if there are enough materials allocated, otherwise a
        ValueError exception will be raised.

        :param quantity: the quantity that will be produced.
        """
        assert self.can_produce(quantity)

        # check if its ok to produce before consuming material
        if self.product.has_quality_tests():
            # We have some quality tests to assure. Register it for later
            assert produced_by
            assert len(serials) == quantity

        self.store.savepoint(u'before_produce')

        for component in self.get_components():
            material = self._get_material_from_component(component)
            needed_material = quantity * component.quantity

            try:
                material.consume(needed_material)
            except ValueError:
                self.store.rollback_to_savepoint(u'before_produce')
                raise

        if self.product.has_quality_tests():
            for serial in serials:
                ProductionProducedItem(store=self.store,
                                       order=self.order,
                                       product=self.product,
                                       produced_by=produced_by,
                                       produced_date=localnow(),
                                       serial_number=serial,
                                       entered_stock=False)
        else:
            # There are no quality tests for this product. Increase stock
            # right now.
            storable = self.product.storable
            storable.increase_stock(quantity, self.order.branch,
                                    StockTransactionHistory.TYPE_PRODUCTION_PRODUCED,
                                    self.id)
        self.produced += quantity
        self.order.try_finalize_production()
        ProductHistory.add_produced_item(self.store, self.order.branch, self)

    def add_lost(self, quantity):
        """Adds a quantity that was lost. The maximum quantity that can be
        lost is the total quantity minus the quantity already produced.

        :param quantity: the quantity that was lost.
        """
        if self.lost + quantity > self.quantity - self.produced:
            raise ValueError(
                _(u'Can not lost more items than the total production quantity.'))

        store = self.store
        store.savepoint(u'before_lose')

        for component in self.get_components():
            material = self._get_material_from_component(component)
            try:
                material.add_lost(quantity * component.quantity)
            except ValueError:
                store.rollback_to_savepoint(u'before_lose')
                raise

        self.lost += quantity
        self.order.try_finalize_production()
        ProductHistory.add_lost_item(store, self.order.branch, self)


@implementer(IDescribable)
class ProductionMaterial(Domain):
    """Production Material object implementation.

    This represents the material needed by a production. It can either be
    consumed or lost (due to manufacturing process).

    """
    __storm_table__ = 'production_material'

    product_id = IdCol()

    #: The |product| that will be consumed.
    product = Reference(product_id, 'Product.id')

    order_id = IdCol()
    #: The |production| that will consume this material.
    order = Reference(order_id, 'ProductionOrder.id')

    # The quantity needed of this material.
    needed = QuantityCol(default=1)

    #: The quantity that is actually allocated to this production. It may be
    #: more than the quantity required (and in this case, the remaining quantity
    #: will be returned to the stock later.
    allocated = QuantityCol(default=0)

    #: The quantity already used of this material.
    consumed = QuantityCol(default=0)

    #: The quantity lost of this material.
    lost = QuantityCol(default=0)

    #: The quantity to purchase of this material.
    to_purchase = QuantityCol(default=0)

    #: The quantity to manufacture of this material.
    to_make = QuantityCol(default=0)

    #
    # Public API
    #

    def can_add_lost(self, quantity):
        """Returns if we can loose a certain quantity of this material.

        :param quantity: the quantity that will be lost.
        """
        return self.can_consume(quantity)

    def can_consume(self, quantity):
        assert quantity > 0
        if self.order.status != ProductionOrder.ORDER_PRODUCING:
            return False

        return self.lost + quantity <= self.needed - self.consumed

    def allocate(self, quantity=None):
        """Allocates the needed quantity of this material by decreasing the
        stock quantity. If no quantity was specified, it will decrease all the
        stock needed or the maximum quantity available. Otherwise, allocate the
        quantity specified or raise a ValueError exception, if the quantity is
        not available.

        :param quantity: the quantity to be allocated or None to allocate the
                         maximum quantity possible.
        """
        storable = self.product.storable
        # If there is no storable for the product, than we just need to allocate
        # what is necessary
        if not storable:
            self.allocated = self.needed
            return

        stock = self.get_stock_quantity()
        if quantity is None:
            required = self.needed - self.allocated
            if stock > required:
                quantity = required
            else:
                quantity = stock
        elif quantity > stock:
            raise ValueError(_(u'Can not allocate this quantity.'))

        if quantity > 0:
            self.allocated += quantity
            storable.decrease_stock(quantity, self.order.branch,
                                    StockTransactionHistory.TYPE_PRODUCTION_ALLOCATED,
                                    self.id)

    def return_remaining(self):
        """Returns remaining allocated material to the stock

        This should be called only after the production order is closed.
        """
        assert self.order.status == ProductionOrder.ORDER_CLOSED
        remaining = self.allocated - self.lost - self.consumed
        assert remaining >= 0
        if not remaining:
            return
        storable = self.product.storable
        if not storable:
            return
        storable.increase_stock(remaining, self.order.branch,
                                StockTransactionHistory.TYPE_PRODUCTION_RETURNED,
                                self.id)
        self.allocated -= remaining

    def add_lost(self, quantity):
        """Adds the quantity lost of this material. The maximum quantity that
        can be lost is given by the formula::

            - max_lost(quantity) = needed - consumed - lost - quantity

        :param quantity: the quantity that was lost.
        """
        assert quantity > 0

        if self.lost + quantity > self.needed - self.consumed:
            raise ValueError(_(u'Cannot loose this quantity.'))

        required = self.consumed + self.lost + quantity
        if required > self.allocated:
            self.allocate(required - self.allocated)

        self.lost += quantity
        store = self.store
        ProductHistory.add_lost_item(store, self.order.branch, self)

    def consume(self, quantity):
        """Consumes a certain quantity of material. The maximum quantity
        allowed to be consumed is given by the following formula:

            - max_consumed(quantity) = needed - consumed - lost - quantity

        :param quantity: the quantity to be consumed.
        """
        assert quantity > 0

        available = self.allocated - self.consumed - self.lost
        if quantity > available:
            raise ValueError(_(u'Can not consume this quantity.'))

        required = self.consumed + self.lost + quantity
        if required > self.allocated:  # pragma nocover
            self.allocate(required - self.allocated)

        self.consumed += quantity
        store = self.store
        ProductHistory.add_consumed_item(store, self.order.branch, self)

    #
    # IDescribable Implementation
    #

    def get_description(self):
        return self.product.sellable.get_description()

    # Accessors

    @property
    def unit_description(self):
        return self.product.sellable.unit_description

    def get_stock_quantity(self):
        storable = self.product.storable
        assert storable is not None
        return storable.get_balance_for_branch(self.order.branch)


@implementer(IDescribable)
class ProductionService(Domain):
    """Production Service object implementation.
    """

    __storm_table__ = 'production_service'

    service_id = IdCol()

    #: The service that will be used by the production.
    service = Reference(service_id, 'Service.id')

    order_id = IdCol()

    #: The :class:`ProductionOrder` of this service.
    order = Reference(order_id, 'ProductionOrder.id')

    #: The service's quantity.
    quantity = QuantityCol(default=1)

    #
    # IDescribable Implementation
    #

    def get_description(self):
        return self.service.sellable.get_description()

    # Properties

    @property
    def unit_description(self):
        return self.service.sellable.unit_description

    @property
    def sellable(self):
        return self.service.sellable


class ProductionProducedItem(Domain):
    """This class represents a composed product that was produced, but
    didn't enter the stock yet. Its used mainly for the quality assurance
    process
    """

    __storm_table__ = 'production_produced_item'

    order_id = IdCol()
    order = Reference(order_id, 'ProductionOrder.id')
    # ProductionItem already has a reference to Product, but we need it for
    # constraint checks UNIQUE(product_id, serial_number)
    product_id = IdCol()
    product = Reference(product_id, 'Product.id')
    produced_by_id = IdCol()
    produced_by = Reference(produced_by_id, 'LoginUser.id')
    produced_date = DateTimeCol()
    serial_number = IntCol()
    entered_stock = BoolCol(default=False)
    test_passed = BoolCol(default=False)
    test_results = ReferenceSet('id', 'ProductionItemQualityResult.produced_item_id')

    def get_pending_tests(self):
        tests_done = set([t.quality_test for t in self.test_results])
        all_tests = set(self.product.quality_tests)
        return list(all_tests.difference(tests_done))

    @classmethod
    def get_last_serial_number(cls, product, store):
        return store.find(cls, product=product).max(cls.serial_number) or 0

    @classmethod
    def is_valid_serial_range(cls, product, first, last, store):
        query = And(cls.product_id == product.id,
                    cls.serial_number >= first,
                    cls.serial_number <= last)
        # There should be no results for the range to be valid
        return store.find(cls, query).is_empty()

    def send_to_stock(self):
        # Already is in stock
        if self.entered_stock:
            return

        storable = self.product.storable
        storable.increase_stock(1, self.order.branch,
                                StockTransactionHistory.TYPE_PRODUCTION_SENT,
                                self.id)
        self.entered_stock = True

    def set_test_result_value(self, quality_test, value, tester):
        store = self.store
        result = store.find(ProductionItemQualityResult,
                            quality_test=quality_test,
                            produced_item=self).one()
        if not result:
            result = ProductionItemQualityResult(
                store=self.store,
                quality_test=quality_test,
                produced_item=self,
                tested_by=tester,
                result_value=u'')
        else:
            result.tested_by = tester

        result.tested_date = localnow()
        result.set_value(value)
        return result

    def get_test_result(self, quality_test):
        store = self.store
        return store.find(ProductionItemQualityResult,
                          quality_test=quality_test,
                          produced_item=self).one()

    def check_tests(self):
        """Checks if all tests for this produced items passes.

        If all tests passes, sets self.test_passed = True
        """
        results = [i.test_passed for i in self.test_results]

        passed = all(results)
        self.test_passed = (passed and
                            len(results) == self.product.quality_tests.count())
        if self.test_passed:
            self.order.try_finalize_production()


@implementer(IDescribable)
class ProductionItemQualityResult(Domain):
    """This table stores the test results for every produced item.
    """

    __storm_table__ = 'production_item_quality_result'

    produced_item_id = IdCol()
    produced_item = Reference(produced_item_id, 'ProductionProducedItem.id')
    quality_test_id = IdCol()
    quality_test = Reference(quality_test_id, 'ProductQualityTest.id')
    tested_by_id = IdCol()
    tested_by = Reference(tested_by_id, 'LoginUser.id')
    tested_date = DateTimeCol(default=None)
    result_value = UnicodeCol()
    test_passed = BoolCol(default=False)

    def get_description(self):
        return self.quality_test.description

    @property
    def result_value_str(self):
        return _(self.result_value)

    def get_boolean_value(self):
        if self.result_value == u'True':
            return True
        elif self.result_value == u'False':
            return False
        else:
            raise ValueError

    def get_decimal_value(self):
        return Decimal(self.result_value)

    def set_value(self, value):
        if isinstance(value, bool):
            self.set_boolean_value(value)
        else:
            self.set_decimal_value(value)

    def set_boolean_value(self, value):
        self.test_passed = self.quality_test.result_value_passes(value)
        self.result_value = unicode(value)
        self.produced_item.check_tests()

    def set_decimal_value(self, value):
        self.test_passed = self.quality_test.result_value_passes(value)
        self.result_value = u'%s' % (value, )
        self.produced_item.check_tests()


class ProductionOrderProducingView(Viewable):

    id = ProductionOrder.id

    tables = [
        ProductionOrder,
        Join(ProductionItem, ProductionOrder.id == ProductionItem.order_id),
    ]

    clause = (ProductionOrder.status == ProductionOrder.ORDER_PRODUCING)

    @classmethod
    def is_product_being_produced(cls, product):
        query = ProductionItem.product_id == product.id
        return not product.store.find(cls, query).is_empty()
