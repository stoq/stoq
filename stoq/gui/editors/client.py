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
## Author(s): Henrique Romano           <henrique@async.com.br>
##            Evandro Vale Miquelito    <evandro@async.com.br>
##
"""
stoq/gui/editors/client.py

    Base classes to client editors
"""

import gettext

from stoq.gui.templates.person import BasePersonRoleEditor
from stoq.gui.slaves.client import ClientStatusSlave
from stoq.domain.person import Person
from stoq.domain.interfaces import IIndividual, IClient

_ = gettext.gettext

class ClientEditor(BasePersonRoleEditor):
    model_name = _('Client')
    model_type = Person.getAdapterClass(IClient)
    gladefile = 'BaseTemplate'
    widgets = ('main_holder', )

    #
    # BaseEditor hooks
    #

    def create_model(self, conn):
        # XXX: Waiting fix for bug #2043.  We should create a Client
        # object not persistent (in this way, we don't need create
        # Person object and its Individual facet).
        person = Person(name="", connection=conn)
        individual = person.addFacet(IIndividual, connection=conn)
        return person.addFacet(IClient, connection=conn)

    def setup_slaves(self):
        BasePersonRoleEditor.setup_slaves(self)
        self.status_slave = ClientStatusSlave(self.conn, self.model)
        self.main_slave.attach_person_slave(self.status_slave)
