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
from unittest import mock


@mock.patch('stoqlib.domain.receiving.ProductHistory.add_received_item')
def test_add_stock_items_without_manage_stock(mock_add_received_item, example_creator):
    sellable = example_creator.create_sellable()
    order = example_creator.create_receiving_order()
    sellable.product.manage_stock = False
    order_item = example_creator.create_receiving_order_item(receiving_order=order,
                                                             sellable=sellable)
    order_item.add_stock_items(example_creator.create_user())
    assert mock_add_received_item.call_count == 0
