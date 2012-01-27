# -*- coding: utf-8 -*-
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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

import inspect
import gc

from kiwi.python import Settable
from kiwi.ui.wizard import WizardStep
from twisted.trial.unittest import SkipTest

from stoqlib.api import api
from stoqlib.lib.introspection import get_all_classes
from stoqlib.gui.editors.baseeditor import BaseEditor, BaseEditorSlave
from stoqlib.domain.person import Person

from stoqlib.domain.test.domaintest import DomainTest


def get_all_slaves():
    slaves = []
    for klass in get_all_classes('stoqlib/gui'):
        try:
            if not issubclass(klass, BaseEditorSlave):
                continue
        except TypeError:
            continue
        if klass.__name__[0] == '_':
            continue
        if klass in [BaseEditor, BaseEditorSlave]:
            continue
        if issubclass(klass, (WizardStep, )):
            continue
        if klass in slaves:
            continue
        slaves.append(klass)
    return slaves


def _test_slave(self, slave):
    args, varargs, varkw, defaults = inspect.getargspec(slave.__init__)
    if not args:
        return

    defaults = defaults or []
    send = []
    for i, arg in enumerate(args[1:]):
        n = len(args) - i - 2
        has_default = n < len(defaults)
        def_idx = i - (len(args) - len(defaults)) + 1
        if arg in ['conn', 'trans']:
            value = self.trans
        elif arg == 'model':
            if slave.model_type is None:
                model_type = slave.model_iface
            else:
                model_type = slave.model_type

            if slave.create_model == BaseEditor.create_model:
                needs_model = True
            else:
                needs_model = False

            if needs_model:
                model = self.create_by_type(model_type)
                if model is None:
                    raise SkipTest('unsupported model: %s' % (model_type.__name__, ))
            else:
                model = None
            value = model
        elif arg == 'station':
            value = api.get_current_station(self.trans)
        elif arg == 'user':
            value = api.get_current_user(self.trans)
        elif arg == 'person':
            value = self.create_person()
        elif arg == 'branch':
            value = self.create_branch()
        elif arg == 'branches':
            value = [self.create_branch()]
        elif arg == 'product':
            value = self.create_product()
        elif arg == 'sale':
            value = self.create_sale()
        elif arg == 'employee':
            value = self.create_employee()
        elif arg == 'payments':
            value = [self.create_payment()]
        elif arg == 'sale_items':
            value = [self.create_sale_item()]
        elif arg == 'products':
            value = [self.create_product()]
        elif arg == 'account':
            value = self.create_account()
        elif arg == 'visual_mode':
            value = True
        elif arg == 'edit_mode':
            value = True
        elif arg == 'confirm_password':
            value = True
        elif arg == 'parent':
            value = None
        elif arg == 'role_type':
            value = Person.ROLE_INDIVIDUAL
        elif has_default:
            value = defaults[def_idx]
        else:
            raise SkipTest('unknown argument: %s' % (arg, ))
        send.append(value)

    s = slave(*send)
    s.on_confirm()


def _create_slave_test():
    TODO = {}
    SKIP = {
        'PaymentEditor': 'Base Class for other editors',
        'BranchDialog': 'cannot provide ICurrentBranch twice',
        'BranchEditor': ' ',
        'CreditProviderEditor': ' ',
        'ICMSTemplateSlave': 'Unkown type',
        'IPITemplateSlave': 'Unkown type',
        'InConsignmentItemEditor': ' ',
        'IndividualEditorTemplate': 'Missing slave',
        'CompanyEditorTemplate': 'Missing slave',
        'ProductStockHistoryDialog': ' ',
        'SaleItemICMSSlave': 'Unkown type',
        'SaleItemIPISlave': 'Unkown type',
        'SaleReturnDetailsDialog': ' ',
        'TillClosingEditor': 'requires an open till',
        'AccountTransactionEditor': 'needs to set a value',
        'PurchaseInstallmentConfirmationSlave': 'pending payment',
        'SaleInstallmentConfirmationSlave': 'pending payment',
        'EmployeeEditor': 'bank account',
        'EmployeeDetailsSlave': 'bank account',
        }
    namespace = dict(_test_slave=_test_slave)

    for slave in get_all_slaves():
        args = inspect.getargspec(slave.__init__)[0]
        if 'wizard' in args or 'model_type' in args:
            continue
        if slave.model_iface is None and slave.model_type is None:
            continue
        if slave.model_type is Settable:
            continue
        tname = slave.__name__
        name = 'test' + tname
        func = lambda self, s=slave: self._test_slave(s)
        func.__name__ = name
        if tname in TODO:
            func.todo = TODO[tname]
        elif tname in SKIP:
            func.skip = SKIP[tname]
        namespace[name] = func

    return type('TestSlaves', (DomainTest, ), namespace)

# Speculative fix: collect the garbage before we run the tests, since there is
# a strange (and random) segmentation fault, due to memory violation.
gc.collect()

TestSlaves = _create_slave_test()
