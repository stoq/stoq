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

from kiwi.ui.objectlist import Column

from stoqlib.domain.person import ContactInfo
from stoqlib.gui.base.lists import ModelListDialog, ModelListSlave
from stoqlib.gui.editors.contacteditor import ContactInfoEditor
from stoqlib.lib.translation import stoqlib_gettext

_ = stoqlib_gettext


class _ContactInfoListSlave(ModelListSlave):
    model_type = ContactInfo
    editor_class = ContactInfoEditor
    columns = [Column('description', title=_('Description'),
                      data_type=str, expand=True),
               Column('contact_info', title=_('Contact Info'),
                      data_type=str, width=200)]

    def populate(self):
        return self.parent.person.contact_infos

    def run_editor(self, store, model):
        store.savepoint('before_run_editor_contacts')
        person = self.parent.person
        retval = self.run_dialog(ContactInfoEditor, model=model,
                                 person=store.fetch(person), store=store)
        if not retval:
            store.rollback_to_savepoint('before_run_editor_contacts')
        return retval


class ContactInfoListDialog(ModelListDialog):
    list_slave_class = _ContactInfoListSlave
    title = _("Contacts")
    size = (500, 250)

    def __init__(self, store, person, reuse_store=False):
        self.person = person
        self.store = store
        ModelListDialog.__init__(self, store, reuse_store=reuse_store)
