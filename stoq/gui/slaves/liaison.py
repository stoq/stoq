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
gui/slaves/liaison.py:

        Liaison slave implementation.
"""


from stoqlib.gui.lists import AdditionListSlave
from kiwi.ui.widgets.list import Column

from stoq.gui.editors.contact import ContactEditor
from stoq.domain.person import Liaison


class LiaisonListSlave(AdditionListSlave):

    def __init__(self, conn, liaison_list=None):
        AdditionListSlave.__init__(self, conn, self, ContactEditor,
                                   self.get_columns(), liaison_list)

    def get_columns(self):
        return [Column('name', title=_('Name'),
                       data_type=str, expand=True),
                Column('phone_number', title=_('Phone Number'),
                       data_type=str, width=200)]

    def get_liaisons(self):
        return self.klist



    #
    # AdditionListSlave hooks
    # 



    def before_delete_items(self, items):
        for item in items:
            Liaison.delete(item.id, connection=self.conn)

    def on_add_item(self, item):
        pass


