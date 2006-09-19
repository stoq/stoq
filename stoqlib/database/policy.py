# -*- Mode: Python; coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006 Async Open Source <http://www.async.com.br>
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
## Author(s):   Johan Dahlin      <jdahlin@async.com.br>
##

from stoqlib.enums import SyncPolicy

_policies = []

class SynchronizationPolicy(object):
    """
    A SynchronizationPolicy contains a list of policies
    for all tables in the database which says how they
    should be synchronized.
    @cvar name: name representing the policy
    @cvar tables: list of tuples, table, policy
    """

class Shop(SynchronizationPolicy):
    name = 'shop'
    tables = [
        ('transaction.TransactionEntry', SyncPolicy.FROM_SOURCE),

        ('profile.UserProfile', SyncPolicy.INITIAL),
        ('profile.ProfileSettings', SyncPolicy.INITIAL),

        ('person.EmployeeRole', SyncPolicy.FROM_SOURCE),
        ('person.Person', SyncPolicy.BOTH),
        ('station.BranchStation', SyncPolicy.FROM_SOURCE),

        ('sellable.BaseSellableInfo', SyncPolicy.FROM_SOURCE),
        ('sellable.OnSaleInfo', SyncPolicy.FROM_SOURCE),
        ('sellable.SellableUnit', SyncPolicy.FROM_SOURCE),
        ('sellable.BaseSellableCategory', SyncPolicy.FROM_SOURCE),
        ('sellable.SellableCategory', SyncPolicy.FROM_SOURCE),

        ('product.Product', SyncPolicy.FROM_SOURCE),
        ('product.ProductSupplierInfo', SyncPolicy.FROM_SOURCE),
        ('product.ProductStockItem', SyncPolicy.FROM_SOURCE),
        ('product.ProductRetentionHistory', SyncPolicy.FROM_SOURCE),

        ('giftcertificate.GiftCertificate', SyncPolicy.INITIAL),

        ('service.Service', SyncPolicy.FROM_SOURCE),
        ('sale.Sale', SyncPolicy.FROM_TARGET),
        ('parameter.ParameterData', SyncPolicy.INITIAL),

        ("fiscal.CfopData", SyncPolicy.INITIAL),
        ('payment.destination.PaymentDestination', SyncPolicy.INITIAL),
        ('account.BankAccount', SyncPolicy.INITIAL),
        ('payment.methods.PaymentMethod', SyncPolicy.INITIAL),
        ('payment.methods.AbstractPaymentMethodAdapter', SyncPolicy.INITIAL),
        ('payment.methods.PaymentMethodDetails', SyncPolicy.INITIAL),
        ]

_policies.append(Shop)

def get_policy_by_name(name):
    """
    Fetches a policy or raises LookupError if a policy cannot
    be found.
    @param name: name of the polic
    @returns: the policy
    @rtype: SynchronizationPolicy
    """

    for policy in _policies:
        if policy.name == name:
            return policy

    raise LookupError(name)
