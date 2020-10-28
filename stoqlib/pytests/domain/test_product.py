# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

#
# Copyright (C) 2006-2020 Async Open Source <http://www.async.com.br>
# All rights reserved
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., or visit: http://www.gnu.org/.
#
#  Author(s): Stoq Team <stoq-devel@async.com.br>
#
import pytest
from unittest import mock

from stoqlib.api import api
from stoqlib.domain.product import StockTransactionHistory
from stoqlib.exceptions import StockError


def test_decrease_stock_without_allow_negative_param(example_creator, current_branch):
    user = example_creator.create_user()
    item = example_creator.create_product_stock_item()
    sale_item = example_creator.create_sale_item()
    assert item.quantity == 0
    with pytest.raises(StockError):
        item.storable.decrease_stock(branch=current_branch,
                                     user=user,
                                     type=StockTransactionHistory.TYPE_SELL,
                                     quantity=2,
                                     object_id=sale_item.id)


def test_decrease_stock_with_allow_negative_param(example_creator, current_branch):
    api.sysparam.get_bool = mock.Mock(return_value=True)
    user = example_creator.create_user()
    item = example_creator.create_product_stock_item()
    sale_item = example_creator.create_sale_item()
    assert item.quantity == 0
    item.storable.decrease_stock(branch=current_branch,
                                 user=user,
                                 type=StockTransactionHistory.TYPE_SELL,
                                 quantity=2,
                                 object_id=sale_item.id)
    assert item.quantity == -2


def test_decrease_stock_without_product_stock_item(example_creator, current_branch):
    api.sysparam.get_bool = mock.Mock(return_value=True)
    user = example_creator.create_user()
    storable = example_creator.create_storable()
    sale_item = example_creator.create_sale_item()
    item = storable.decrease_stock(
        branch=current_branch,
        user=user,
        type=StockTransactionHistory.TYPE_SELL,
        quantity=2,
        object_id=sale_item.id)
    assert item.quantity == -2


def test_increase_decrease_stock(example_creator, current_branch, current_user):
    stock_item = example_creator.create_product_stock_item()
    assert stock_item.quantity == 0
    assert stock_item.stock_cost == 0

    storable = stock_item.storable
    storable.increase_stock(1, current_branch, StockTransactionHistory.TYPE_INVENTORY_ADJUST,
                            None, current_user, 0)
    assert stock_item.quantity == 1
    assert stock_item.stock_cost == 0

    storable.increase_stock(1, current_branch, StockTransactionHistory.TYPE_RECEIVED_PURCHASE,
                            None, current_user, unit_cost=10)
    stock_item = storable.get_stock_item(current_branch, None)
    assert stock_item.quantity == 2
    assert stock_item.stock_cost == 5

    stock_item = storable.decrease_stock(1, current_branch,
                                         StockTransactionHistory.TYPE_SELL,
                                         None, current_user)
    assert stock_item.quantity == 1
    assert stock_item.stock_cost == 5

    storable.increase_stock(1, current_branch, StockTransactionHistory.TYPE_RECEIVED_PURCHASE,
                            None, current_user, unit_cost=15)
    assert stock_item.quantity == 2
    # 10 is the weighted average of the previous and current stock.
    assert stock_item.stock_cost == 10

    stock_item = storable.decrease_stock(2, current_branch,
                                         StockTransactionHistory.TYPE_SELL,
                                         None, current_user)
    # Even though the quantity is zero, we keep the last stock_cost
    assert stock_item.quantity == 0
    assert stock_item.stock_cost == 10

    storable.increase_stock(1, current_branch, StockTransactionHistory.TYPE_RECEIVED_PURCHASE,
                            None, current_user, unit_cost=20)
    # The stock_cost is the same as the new unit_cost, since previous quantity was zero
    assert stock_item.quantity == 1
    assert stock_item.stock_cost == 20


def test_when_current_quantity_is_negative_and_purchase_changes_to_positive(
        example_creator, current_branch, current_user):
    stock_item = example_creator.create_product_stock_item(quantity=-2, stock_cost=5)
    assert stock_item.quantity == -2
    assert stock_item.stock_cost == 5

    storable = stock_item.storable
    storable.increase_stock(3, current_branch, StockTransactionHistory.TYPE_RECEIVED_PURCHASE,
                            None, current_user, unit_cost=20)
    # The stock_cost is the same as the new unit_cost because the previous quantity
    # is negative so we ignore the last stock_cost
    assert stock_item.quantity == 1
    assert stock_item.stock_cost == 20


def test_when_quantity_changes_to_negative_them_back_to_positive(
        example_creator, current_branch, current_user):
    stock_item = example_creator.create_product_stock_item(quantity=1, stock_cost=5)

    storable = stock_item.storable
    stock_item = storable.decrease_stock(2, current_branch,
                                         StockTransactionHistory.TYPE_SELL,
                                         None, current_user)
    assert stock_item.quantity == -1
    assert stock_item.stock_cost == 5

    storable.increase_stock(2, current_branch, StockTransactionHistory.TYPE_RECEIVED_PURCHASE,
                            None, current_user, unit_cost=15)
    # The stock_cost is the same as the new unit_cost because the previous quantity
    # is negative so we ignore the last stock_cost
    assert stock_item.quantity == 1
    assert stock_item.stock_cost == 15


def test_weighted_average_calc(example_creator, current_branch, current_user):
    stock_item = example_creator.create_product_stock_item(quantity=4, stock_cost=10)
    assert stock_item.quantity == 4
    assert stock_item.stock_cost == 10

    storable = stock_item.storable
    storable.increase_stock(6, current_branch, StockTransactionHistory.TYPE_RECEIVED_PURCHASE,
                            None, current_user, unit_cost=15)
    assert stock_item.quantity == 10
    # 13 is the weighted average of the previous and current stock.
    # (4*10 + 6*15)/(4+6) = 13
    assert stock_item.stock_cost == 13


def test_register_initial_stock_with_negative_quantity(
        example_creator, current_branch, current_user):
    storable = example_creator.create_storable()
    with pytest.raises(ValueError):
        storable.register_initial_stock(-3, current_branch, 5, current_user)
