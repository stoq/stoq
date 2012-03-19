# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005-2008 Async Open Source <http://www.async.com.br>
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
##
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##
""" Interfaces definition for all domain classes """

from zope.interface import Attribute, Interface

# pylint: disable=E0102,E0211,E0213

#
# Interfaces
#


class IActive(Interface):
    """It defines if a certain object can be active or not"""

    is_active = Attribute('This attribute defines if the object is active')

    def inactivate():
        """Inactivate an active object"""

    def activate():
        """Activate an inactive object"""

    def get_status_string():
        """Active or Inactive in the specific locale"""


class IContainer(Interface):
    """An objects that holds other objects or items"""

    def add_item(item):
        """Add a persistent or non-persistent item associated with this
        model."""

    def get_items():
        """Get all the items in the container. The result value could be a
        simple python list or an instance which maps to SQL statement.  """

    def remove_item(item):
        """Remove from the list or database the item desired."""


class IDescribable(Interface):
    """It defines that a object can be described through get_description
    method.
    """
    def get_description():
        """ Returns a description that identifies the object """


class IORMObject(Interface):
    id = Attribute("Object ID")

    def delete(obj_id, connection):
        pass


class IPaymentTransaction(Interface):
    """ Interface specification for PaymentGroups. """

    def confirm():
        """Transaction is confirmed.
        Payments might occur at this time, in case of money payment,
        others may happen later
        """

    def pay():
        """All payment for this transaction are paid.
        """

    def cancel():
        """Cancels the transaction before it's completed.
        """

    def return_(renegotiation):
        """Returns the goods purchased.
        This means that all paid payments are paid back and
        all pending onces are cancelled.
        Commissions may also reversed.
        :param renegotiation: renegotiation data
        """


class IReversal(Interface):
    """A financial entry which support reversal operations"""

    def reverse_entry(invoice_number):
        """Takes a financial entry and reverse it, creating a new instance
        with an oposite value
        """
