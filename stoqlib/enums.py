# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4


##
## Copyright (C) 2005, 2006 Async Open Source <http://www.async.com.br>
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
""" Database enums """

from kiwi.python import enum


class SyncPolicy(enum):
    #
    # Source -> Master/Office
    # Target -> Slave/Store
    #

    """
        - I{FROM_SOURCE}: from the source to the target
        - I{FROM_TARGET}: from the target to the source
        - I{BOTH}: in both directions
        - I{INITIAL}: only when doing the initial clone

    """
    (FROM_SOURCE,
     FROM_TARGET,
     BOTH,
     INITIAL) = range(4)


class CreatePaymentStatus(enum):
    """
    Anyone who catches CreatePaymentEvent should return one of this.
    """

    (SUCCESS,
     FAIL,
     UNHANDLED, ) = range(3)


class NFeDanfeOrientation(enum):
    (PORTRAIT,
     LANDSCAPE, ) = range(2)


class ReturnPolicy(enum):
    """Policy for returning sales.

    This enum is used by the :class:`parameter
    <stoqlib.lib.parameters.ParameterDetails>` RETURN_POLICY_ON_SALES.
    """
    (CLIENT_CHOICE,
     RETURN_MONEY,
     RETURN_CREDIT, ) = range(3)


class LatePaymentPolicy(enum):
    """Policy for clients with late payments

    This enum is used by the :class:`parameter
    <stoqlib.lib.parameters.ParameterDetails>` LATE_PAYMENTS_POLICY.
    """
    (ALLOW_SALES,
     DISALLOW_STORE_CREDIT,
     DISALLOW_SALES) = range(3)


class ChangeSalespersonPolicy(enum):
    """Policy for changing the |salesperson| on POS sales

    This enum is used by the :class:`parameter
    <stoqlib.lib.parameters.ParameterDetails>` ACCEPT_CHANGE_SALESPERSON
    """

    (DISALLOW,
     ALLOW,
     FORCE_CHOOSE) = range(3)


class SearchFilterPosition(enum):
    """
    An enum used to indicate where a search filter should be added to
    a SearchContainer::

      - TOP: top left corner
      - BOTTOM: bottom
    """
    (TOP,
     BOTTOM) = range(2)
