# -*- Mode: Python; coding: iso-8859-1 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2004 Async Open Source <http://www.async.com.br>
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
## Author(s):   Daniel Saran R. da Cunha    <daniel@async.com.br>
##              Henrique Romano             <henrique@async.com.br>
##
"""
gui/editors/person/employee.py
    
    Employee editor implementation.
"""


import gettext

from stoqlib.gui.editors import BaseEditor

from stoq.gui.templates.person import IndividualEditorTemplate
from stoq.domain.interfaces import IIndividual, IEmployee
from stoq.domain.person import (PersonAdaptToEmployee,
                                Person)
from stoq.gui.slaves.employee import (EmployeeDetailsSlave,
                                      EmployeeStatusSlave)

_ = gettext.gettext

class EmployeeEditor(BaseEditor):
    title = _('Employee Editor')
    model_type = PersonAdaptToEmployee
    gladefile = 'BaseTemplate'
    widgets = ('main_holder', )

    def create_model(self, conn):
        # XXX: Waiting fix for bug #2043. We should create a Employee
        # object not persistent (int this way, we don't need create a
        # Person object and its dependencies).
        person = Person(name='', connection=conn)
        individual = person.addFacet(IIndividual, connection=conn)
        return person.addFacet(IEmployee, connection=conn,
                               position=None)
    def setup_slaves(self):
        individual = IIndividual(self.model.get_adapted(),
                                 connection=self.conn)
        self.individual_slave = IndividualEditorTemplate(self.conn, individual)
        self.attach_slave('main_holder', self.individual_slave)

        label = _('Employee Data')
        self.individual_slave.show_custom_holder(label)

        self.details_slave = EmployeeDetailsSlave(self.conn, self.model)
        self.individual_slave.attach_custom_slave(self.details_slave)

        self.status_slave = EmployeeStatusSlave(self.conn, self.model)
        self.individual_slave.attach_person_slave(self.status_slave)
        
    def on_confirm(self):
        self.individual_slave.on_confirm()
        return self.model
