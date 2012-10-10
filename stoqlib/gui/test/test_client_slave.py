# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2012 Async Open Source <http://www.async.com.br>
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

from stoqlib.gui.slaves.clientslave import ClientStatusSlave
from stoqlib.gui.uitestutils import GUITest
from stoqlib.lib.parameters import sysparam
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class TestClientSlave(GUITest):
    def testShow(self):
        # this is necessary so previous tests will not interfere in here
        sysparam(self.trans).update_parameter(
            "CREDIT_LIMIT_SALARY_PERCENT",
            "0")

        client = self.create_client()
        client.salary = 100
        slave = ClientStatusSlave(self.trans, client)
        self.check_slave(slave, 'slave-clientstatus-show')

    def test_credit_limit_active(self):
        sysparam(self.trans).update_parameter(
            "CREDIT_LIMIT_SALARY_PERCENT",
            "10")

        client = self.create_client()
        slave = ClientStatusSlave(self.trans, client)

        # if CREDIT_LIMIT_SALARY_PERCENT is higher than 0, credit limit
        # should not be editable
        self.assertNotSensitive(slave, ['credit_limit'])

        # if salary percent is 0 credit limit should be editable
        sysparam(self.trans).update_parameter(
            "CREDIT_LIMIT_SALARY_PERCENT",
            "0")
        slave = ClientStatusSlave(self.trans, client)
        self.assertSensitive(slave, ['credit_limit'])

    def test_credit_limit_validate(self):
        client = self.create_client()
        slave = ClientStatusSlave(self.trans, client)

        # checks a valid credit limit
        self.assertEquals(None, slave.credit_limit.emit('validate', 10))
        self.assertEquals(None, slave.credit_limit.emit('validate', 0))

        # checks invalid credit limit
        self.assertEquals("Credit limit must be greater than or equal to 0",
                          str(slave.credit_limit.emit('validate', -10)))

    def test_credit_limit_update(self):
        sysparam(self.trans).update_parameter(
            "CREDIT_LIMIT_SALARY_PERCENT",
            "10")

        client = self.create_client()
        client.salary = 50
        slave = ClientStatusSlave(self.trans, client)
        slave.salary.emit('changed')
        self.assertEquals(slave.credit_limit.read(), 5)

        # checks if credit limit updated correctly when salary changes
        # and parameter salary percent is not 0
        slave.salary.update(100)
        slave.salary.emit('changed')
        self.assertEquals(slave.credit_limit.read(), 10)

        sysparam(self.trans).update_parameter(
            "CREDIT_LIMIT_SALARY_PERCENT",
            "0")

        # checks if credit limit does not update (correct behavior)
        # when salary percent is 0 and salary changes
        credit_limit = 0
        client.credit_limit = credit_limit
        slave.credit_limit.update(credit_limit)
        slave.credit_limit.emit('changed')

        slave.salary.update(200)
        slave.salary.emit('changed')

        self.assertEquals(slave.credit_limit.read(), credit_limit)

    def test_salary_validate(self):
        client = self.create_client()
        slave = ClientStatusSlave(self.trans, client)

        # checks a valid salary
        self.assertEquals(None, slave.salary.emit('validate', 10))

        # checks invalid salary
        self.assertEquals("Salary can't be lower than 0.",
                          str(slave.salary.emit('validate', -10)))
