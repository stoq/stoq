# -*- coding: utf-8 -*-
# vi:si:et:sw=4:sts=4:ts=4

##
## Copyright (C) 2005, 2006 Async Open Source
##
## This program is free software; you can redistribute it and/or
## modify it under the terms of the GNU Lesser General Public License
## as published by the Free Software Foundation; either version 2
## of the License, or (at your option) any later version.
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
##
## Author(s): Stoq Team <stoq-devel@async.com.br>
##

from stoqlib.gui.editors.baseeditor import BaseEditor


class SimpleEntryEditor(BaseEditor):
    """Editor that offers a generic entry to input a string value."""
    gladefile = "SimpleEntryEditor"
    confirm_widgets = ['name_entry']

    def __init__(self, conn, model, attr_name, name_entry_label='Name:',
                 title='', visual_mode=False):
        self.title = title
        self.attr_name = attr_name
        BaseEditor.__init__(self, conn, model, visual_mode=visual_mode)
        self.name_entry_label.set_text(name_entry_label)

    def setup_proxies(self):
        assert self.model
        self.name_entry.set_property('model-attribute', self.attr_name)
        self.add_proxy(model=self.model, widgets=['name_entry'])
