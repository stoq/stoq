# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005 Async Open Source <http://www.async.com.br>
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
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
## Author(s):   Evandro Vale Miquelito     <evandro@async.com.br>
##
"""
stoq/domain/payment/operation.py:

   Payment operation management implementations.
"""

from sqlobject import DateTimeCol, StringCol
from zope.interface import implements

from stoq.domain.base import Domain, ModelAdapter
from stoq.domain.interfaces import IPaymentDevolution, IPaymentDeposit



#
# Domain Classes
# 



class PaymentOperation(Domain):
    """A base class which define general payment operations such deposits
    and devolutions
    """
    operation_date = DateTimeCol()



#
# Adapters
#



class POAdaptToPaymentDevolution(ModelAdapter):
    """Stores information for payment devolutions"""
    implements(IPaymentDevolution)

    reason = StringCol(default='')

    def get_devolution_date(self):
        return self.get_adapted().operation_date

PaymentOperation.registerFacet(POAdaptToPaymentDevolution,
                               IPaymentDevolution)


class POAdaptToPaymentDeposit(ModelAdapter):
    """Stores information for payment deposits"""
    implements(IPaymentDeposit)

    def get_deposit_date(self):
        return self.get_adapted().operation_date

PaymentOperation.registerFacet(POAdaptToPaymentDeposit,
                               IPaymentDeposit)
