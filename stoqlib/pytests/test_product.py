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
