# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2013 Async Open Source <http://www.async.com.br>
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
## GNU General Public License for more details.
##
## You should have received a copy of the GNU Lesser General Public License
## along with this program; if not, write to the Free Software
## Foundation, Inc., or visit: http://www.gnu.org/.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

from storm.references import Reference

from stoqlib.database.properties import IntCol, DecimalCol, DateTimeCol
from stoqlib.domain.base import Domain


class OpticalWorkOrder(Domain):
    """An institution created to publish books"""

    __storm_table__ = 'optical_work_order'

    work_order_id = IntCol()
    work_order = Reference(work_order_id, 'WorkOrder.id')

    prescription_date = DateTimeCol()

    # TODO: gather all information that is necessary and find out the english
    # names.

    # Right Eye
    od_esferico = DecimalCol()

    # Left Eye
    oe_esferico = DecimalCol()
