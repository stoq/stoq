# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2006-2007 Async Open Source <http://www.async.com.br>
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
## Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307,
## USA.
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

from kiwi.ui.widgets.list import Column

from stoqlib.domain.person import Liaison
from stoqlib.gui.base.lists import ModelListDialog, ModelListSlave
from stoqlib.gui.editors.contacteditor import ContactEditor
from stoqlib.lib.formatters import format_phone_number
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class _LiaisonListSlave(ModelListSlave):
    model_type = Liaison
    editor_class = ContactEditor
    columns = [Column('name', title=_('Name'),
                      data_type=str, expand=True),
               Column('phone_number', title=_('Phone Number'),
                      format_func=format_phone_number,
                      data_type=str, width=200)]

    def populate(self):
        return Liaison.selectBy(person=self.parent.person,
                                connection=self.parent.trans)

    def run_editor(self, trans, model):
        trans.savepoint('before_run_editor_liaison')
        person = self.parent.person
        retval = self.run_dialog(ContactEditor, conn=trans,
                                 model=model,
                                 person=trans.get(person))
        if not retval:
            trans.rollback_to_savepoint('before_run_editor_liaison')
        return retval


class LiaisonListDialog(ModelListDialog):
    list_slave_class = _LiaisonListSlave
    title = _("Liasons")
    size = (500, 250)

    def __init__(self, trans, person, reuse_transaction=False):
        self.person = person
        self.trans = trans
        ModelListDialog.__init__(self, trans)
        if reuse_transaction:
            self.list_slave.set_reuse_transaction(trans)
