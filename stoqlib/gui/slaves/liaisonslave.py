# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005, 2006, 2008 Async Open Source <http://www.async.com.br>
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
## Author(s):   Daniel Saran R. da Cunha    <daniel@async.com.br>
##              Henrique Romano             <henrique@async.com.br>
##              Evandro Vale Miquelito      <evandro@async.com.br>
##              Johan Dahlin                <jdahlin@async.com.br>
##

"""Liaison slave implementation"""

from kiwi.ui.widgets.list import Column

from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.base.lists import ModelListDialog
from stoqlib.gui.editors.contacteditor import ContactEditor
from stoqlib.lib.validators import format_phone_number
from stoqlib.domain.person import Liaison

_ = stoqlib_gettext


class LiaisonListDialog(ModelListDialog):

    # ModelListDialog
    model_type = Liaison
    editor_class = ContactEditor
    title = _("Liasons")
    size = (500, 250)

    # ListDialog
    columns = [Column('name', title=_('Name'),
                      data_type=str, expand=True),
               Column('phone_number', title=_('Phone Number'),
                      format_func=format_phone_number,
                      data_type=str, width=200)]

    def __init__(self, trans, person):
        self.person = person
        self.trans = trans
        ModelListDialog.__init__(self, trans)
        self.set_reuse_transaction(trans)

    def populate(self):
        return Liaison.selectBy(person=self.person, connection=self.trans)

    def run_editor(self, trans, model):
        return self.run_dialog(ContactEditor, conn=trans,
                               model=model, person=self.person)
