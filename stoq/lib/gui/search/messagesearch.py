# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2018 Async Open Source <http://www.async.com.br>
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
##  Author(s): Stoq Team <stoq-devel@async.com.br>
##
##
import collections
import datetime

from kiwi.ui.forms import MultiLineField, DateField

from stoqlib.api import api
from stoqlib.domain.message import Message, MessageView
from stoqlib.domain.person import LoginUser, Branch
from stoqlib.lib.decorators import cached_property
from stoqlib.lib.translation import stoqlib_gettext
from stoq.lib.gui.editors.baseeditor import BaseEditor
from stoq.lib.gui.fields import PersonField, UserProfileField
from stoq.lib.gui.search.searchcolumns import SearchColumn
from stoq.lib.gui.search.searcheditor import SearchEditor

_ = stoqlib_gettext


class MessageEditor(BaseEditor):
    model_name = _('Client Category')
    model_type = Message

    @cached_property()
    def fields(self):
        return collections.OrderedDict(
            expire_at=DateField(_('Expire at'), proxy=True),
            branch_id=PersonField(_('Branch'), proxy=True, person_type=Branch),
            profile_id=UserProfileField(_('User profile'), proxy=True),
            user_id=PersonField(_('User'), proxy=True, person_type=LoginUser),
            content=MultiLineField(_('Message'), proxy=True),
        )

    def create_model(self, store):
        return Message(store=store, created_by=api.get_current_user(store))


class MessageSearch(SearchEditor):
    size = (750, 500)
    title = _('Message search')
    search_label = _('Messages matching:')
    search_spec = MessageView
    editor_class = MessageEditor

    #
    #  SearchEditor
    #

    def create_filters(self):
        self.set_text_field_columns(['content'])

    def get_columns(self):
        return [
            SearchColumn("created_at", _("Created at"), data_type=datetime.date,
                         sorted=True),
            SearchColumn("expire_at", _("Expire at"), data_type=datetime.date),
            SearchColumn("creator_name", _("Created by"), data_type=str),
            SearchColumn("content", _("Content"), data_type=str, expand=True),
        ]

    def get_editor_model(self, model):
        """Search Editor hook"""
        return model.message
