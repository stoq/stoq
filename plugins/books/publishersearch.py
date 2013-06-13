# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2010 Async Open Source <http://www.async.com.br>
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
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

""" Search dialog/Editor for publishers """

from stoqlib.lib.translation import stoqlib_gettext
from stoqlib.gui.search.personsearch import BasePersonSearch
from stoqlib.gui.search.searchcolumns import SearchColumn
from stoqlib.gui.templates.persontemplate import BasePersonRoleEditor

from books.booksdomain import BookPublisher, PublisherView

_ = stoqlib_gettext


class PublisherEditor(BasePersonRoleEditor):
    model_name = _(u'Publisher')
    title = _(u'New Publisher')
    model_type = BookPublisher
    gladefile = 'BaseTemplate'

    def create_model(self, store):
        person = BasePersonRoleEditor.create_model(self, store)
        publisher = store.find(BookPublisher, person=person).one()
        if publisher is None:
            publisher = BookPublisher(person=person,
                                      store=store)
        return publisher


class PublisherSearch(BasePersonSearch):
    title = _('Publisher Search')
    editor_class = PublisherEditor
    search_spec = PublisherView
    size = (750, 450)
    search_lbl_text = _('Publishers matching:')
    result_strings = _('publisher'), _('publishers')

    def _get_status_values(self):
        items = [(value, key) for key, value in
                 BookPublisher.statuses.items()]
        items.insert(0, (_('Any'), None))
        return items

    #
    # SearchDialog Hooks
    #

    def create_filters(self):
        self.set_text_field_columns(['name'])

    def get_columns(self):
        return [SearchColumn('name', _('Name'), str, width=250, expand=True)]

    def get_editor_model(self, model):
        return model.publisher
