# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2012 Async Open Source <http://www.async.com.br>
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

"""
Stoq domain classes, the business logic of Stoq.

This package contain a set of domain classes that abstracts the database business logic
into a high-level python syntax that can be used by the rest of the application.

An `Object Relational Mapper <http://en.wikipedia.org/wiki/Object-relational_mapping>`_ (ORM)
is used to translate the `PostgreSQL <http://www.postgresql.org>`_ query statements
to and from Python syntax. We are currently using the `Storm <http://storm.canonical.com/>`_ ORM.

Starting point for the domain classes:

* :py:mod:`stoqlib.domain.account`: bank accounts and transactions
* :py:mod:`stoqlib.domain.address`: address
* :py:mod:`stoqlib.domain.attachment`: files that can be attached
* :py:mod:`stoqlib.domain.base`: base infrastructure
* :py:mod:`stoqlib.domain.commission`: sale commission
* :py:mod:`stoqlib.domain.costcenter`: cost centers
* :py:mod:`stoqlib.domain.devices`: device drivers
* :py:mod:`stoqlib.domain.event`: persistent database logging
* :py:mod:`stoqlib.domain.events`: event APIs
* :py:mod:`stoqlib.domain.exampledata`: example creators
* :py:mod:`stoqlib.domain.fiscal`: fiscal books (with taxes)
* :py:mod:`stoqlib.domain.image`: images
* :py:mod:`stoqlib.domain.interfaces`: class interface definitions
* :py:mod:`stoqlib.domain.inventory`: inventory handling
* :py:mod:`stoqlib.domain.invoice`: invoices and fields
* :py:mod:`stoqlib.domain.loan`: loads
* :py:mod:`stoqlib.domain.parameter`: configuration parameters
* :py:mod:`stoqlib.domain.payment.card`: card payment method related domain
* :py:mod:`stoqlib.domain.payment.category`: user categorization
* :py:mod:`stoqlib.domain.payment.comment`: annotations
* :py:mod:`stoqlib.domain.payment.group`: group/set of payments
* :py:mod:`stoqlib.domain.payment.method`: methods such as money, card, bill etc
* :py:mod:`stoqlib.domain.payment.operation`: operation
* :py:mod:`stoqlib.domain.payment.payment`: main payment class
* :py:mod:`stoqlib.domain.person`: persons
* :py:mod:`stoqlib.domain.plugin`: plugins
* :py:mod:`stoqlib.domain.production`: product manufacturing
* :py:mod:`stoqlib.domain.product`: product
* :py:mod:`stoqlib.domain.profile`: user profiles and permissions
* :py:mod:`stoqlib.domain.purchase`: purchase orders
* :py:mod:`stoqlib.domain.receiving`: receiving orders
* :py:mod:`stoqlib.domain.returnedsale`: trade and returning sales
* :py:mod:`stoqlib.domain.sale`: sale orders
* :py:mod:`stoqlib.domain.sellable`: common database parts for product and service
* :py:mod:`stoqlib.domain.service`: service
* :py:mod:`stoqlib.domain.station`: computers
* :py:mod:`stoqlib.domain.stockdecrease`: manual stock changes
* :py:mod:`stoqlib.domain.synchronization`: database synchronization
* :py:mod:`stoqlib.domain.system`: system tables
* :py:mod:`stoqlib.domain.taxes`: taxes
* :py:mod:`stoqlib.domain.till`: cashier and till
* :py:mod:`stoqlib.domain.transfer`: transfers between different branches
* :py:mod:`stoqlib.domain.uiform`: user interface customizations
* :py:mod:`stoqlib.domain.views`: complex queries grouped into a view
* :py:mod:`stoqlib.domain.workorder`: maintenance work orders
"""
