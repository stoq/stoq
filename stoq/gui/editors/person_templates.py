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
stoq/gui/editors/person_templates.py:

    Templates implementation for person editors.
"""


from stoqlib.gui.editors import BaseEditorSlave
from stoqlib.gui.slaves import NoteSlave

from Stoq2.domain.person import Person


class PersonEditorTemplate(BaseEditorSlave):
    gladefile = 'PersonEditorTemplate'
    proxy_widgets = ('name', 
                     'phone_number',
                     'mobile_number',
                     'fax_number',
                     'email')

    widgets = ('notebook',
               'id_holder',
               'address_holder',
               'person_status_holder',
               'details_holder',
               'contact_list_holder',
               'custom_holder',
               'note_holder',
               'address_button') + proxy_widgets

    def __init__(self, conn, model=None):
        """ model: a Person object or nothing """
        if not model:
            # XXX: Waiting fix for bug #2043
            model = Person(name="", connection=conn)

        BaseEditorSlave.__init__(self, conn, model)

    def attach_model_slave(self, name, slave_type, slave_model):
        self.attach_slave(name, slave_type(self.conn, slave_model))

    #
    # BaseEditorSlave hooks
    #

    def setup_proxies(self):
        self.proxy = self.add_proxy(self.model, self.proxy_widgets)

    def setup_slaves(self):
        self.attach_model_slave('note_holder', NoteSlave, self.model)


