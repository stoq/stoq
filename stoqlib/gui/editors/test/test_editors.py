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
## Author(s):   Johan Dahlin  <jdahlin@async.com.br>
##

import inspect

from kiwi.python import Settable
from kiwi.ui.wizard import WizardStep
from twisted.trial.unittest import SkipTest

from stoqlib.database.runtime import get_current_station, get_current_user
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
        if issubclass(klass, (WizardStep,)):
            continue
        if klass in slaves:
            continue
        slaves.append(klass)
    return slaves

def _test_slave(self, slave):
    args = inspect.getargspec(slave.__init__)[0]
    if not args:
        return

    send = []
    for arg in args[1:]:
        if arg == 'conn':
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
                    raise SkipTest('unsupported model: %s' % (model_type.__name__,))
            else:
                model = None
            value = model
        elif arg == 'station':
            value = get_current_station(self.trans)
        elif arg == 'user':
            value = get_current_user(self.trans)
        elif arg == 'person':
            value = self.create_person()
        elif arg == 'product':
            value = self.create_product()
        elif arg == 'sale':
            value = self.create_sale()
        elif arg == 'employee':
            value = self.create_employee()
        elif arg == 'products':
            value = [self.create_product()]
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
        else:
            raise SkipTest('unknown argument: %s' % (arg,))
        send.append(value)

    s = slave(*send)
    s.on_confirm()

def _create_slave_test():
    TODO = {}
    SKIP = {
        'CashOutEditor': ' ',
        'CashInEditor': ' ',
        'CashAdvanceEditor': '.glade warnings',
        'ProductStockHistoryDialog': ' ',
        'ProductSupplierEditor' : ' ',
        'EmployeeRoleSlave': 'duplicated role histories',
        'SaleCancellationDetailsDialog': ' ',
        'SellableCategoryEditor': 'glade warnings',
        'BranchEditor': ' ',
        'CreditProviderEditor': ' ',
        'UserEditor': ' ',
        'TillClosingEditor': 'requires an open till',
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
        if tname in SKIP:
            func.skip = SKIP[tname]
        namespace[name] = func

    return type('TestSlaves', (DomainTest,), namespace)

TestSlaves = _create_slave_test()
